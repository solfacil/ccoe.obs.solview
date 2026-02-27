import logging
import os
from typing import Optional, Dict
from fastapi import FastAPI
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter as OTLPSpanGrpcExporter
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter as OTLPSpanHttpExporter
from opentelemetry.exporter.otlp.proto.http.trace_exporter import _append_trace_path
from opentelemetry.instrumentation.asyncpg import AsyncPGInstrumentor
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.instrumentation.logging import LoggingInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.sdk.resources import SERVICE_NAME, SERVICE_VERSION, Resource
from opentelemetry.sdk.trace import TracerProvider, sampling
from opentelemetry.semconv.resource import ResourceAttributes
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter, SimpleSpanProcessor
from opentelemetry.trace import set_tracer_provider
from opentelemetry.metrics import set_meter_provider
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.exporter.prometheus import PrometheusMetricReader
from prometheus_fastapi_instrumentator import Instrumentator
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.util.http.httplib import HttpClientInstrumentor
from ..config import get_settings, setup_settings
from ..settings import SolviewSettings

logger = logging.getLogger("solview.tracing.core")


def setup_tracer(app: FastAPI = None) -> TracerProvider:
    """
    Setup do OpenTelemetry tracing provider e instrumentação para FastAPI e libs relacionadas.

    Usa a configuração atual de get_settings(). Para configurar por env antes, use configure_solview() ou setup_tracer_from_env(app).
    """

    settings = get_settings()
    service_name = settings.service_name
    service_version = settings.version
    resource = _get_resource(
        service_name=service_name,
        service_version=service_version,
        deployment_name=settings.environment,
        service_namespace=settings.service_namespace,
    )

    # TracerProvider para tracing
    tracer_provider = TracerProvider(
        sampler=_get_sampler(settings.trace_sampler, settings.trace_sampling_ratio),
        resource=resource,
    )
    set_tracer_provider(tracer_provider)
    logger.info("TracerProvider configurado | Serviço: %s v%s", service_name, service_version)

    # MeterProvider para métricas Prometheus
    prometheus_reader = PrometheusMetricReader()
    metrics_provider = MeterProvider(metric_readers=[prometheus_reader])
    set_meter_provider(metrics_provider)
    logger.info("MeterProvider configurado | Serviço: %s v%s", service_name, service_version)

    python_env = os.getenv("PYTHON_ENV", "")
    if getattr(settings, "use_console_exporter_on_unittest", False) and python_env == "unittest":
        # Usa SimpleSpanProcessor para evitar flush assíncrono em stdout fechado no teardown do pytest
        tracer_provider.add_span_processor(SimpleSpanProcessor(ConsoleSpanExporter()))
        logger.info("[solview.tracing] Modo unittest: ConsoleSpanExporter habilitado.")
        return tracer_provider

    os.environ.setdefault("OTEL_SEMCONV_STABILITY_OPT_IN", "http")

    # Instrumentação automática
    Instrumentator().instrument(app=app).expose(app)
    LoggingInstrumentor().instrument(set_logging_format=True)
    HTTPXClientInstrumentor().instrument()
    AsyncPGInstrumentor().instrument()
    SQLAlchemyInstrumentor().instrument(enable_commenter=settings.otlp_sqlalchemy_enable_commenter, commenter_options={})
    HttpClientInstrumentor().instrument()
    RequestsInstrumentor().instrument()
    if app:
        # Define URLs de infraestrutura que devem ser excluídas do tracing
        excluded_urls = "/metrics|/ready|/info|/docs|/openapi.json|/favicon.ico"
        
        FastAPIInstrumentor().instrument_app(
            app=app, 
            excluded_urls=excluded_urls
        )
        logger.info("[solview.tracing] FastAPI instrumentada para tracing (excluindo URLs de infraestrutura: %s)", excluded_urls)

    # Exportador OTLP
    exporter = _get_otlp_span_exporter(
        protocol=settings.otlp_exporter_protocol,
        host=settings.otlp_exporter_host,
        port=settings.otlp_exporter_port,
        http_encrypted=settings.otlp_exporter_http_encrypted,
        agent_auth_token=settings.otlp_agent_auth_token,
    )
    tracer_provider.add_span_processor(BatchSpanProcessor(exporter))
    logger.info("[solview.tracing] Exportador OTLP conectado: %s://%s:%s", settings.otlp_exporter_protocol, settings.otlp_exporter_host, settings.otlp_exporter_port)
    return tracer_provider


def setup_tracer_from_env(app: FastAPI) -> TracerProvider:
    """
    Garante que get_settings() está preenchido por env e chama setup_tracer(app).
    """
    return setup_tracer(app)


def _get_resource(
    service_name: str,
    service_version: str,
    deployment_name: Optional[str],
    service_namespace: Optional[str],
) -> Resource:
    attrs = {
        SERVICE_NAME: service_name,
        SERVICE_VERSION: service_version,
        ResourceAttributes.SERVICE_NAMESPACE: service_namespace or "solview",
        ResourceAttributes.DEPLOYMENT_ENVIRONMENT: deployment_name,
    }
    logger.info("[solview.tracing] Resource OTEL: %s", attrs)
    return Resource.create(attrs)


def _get_sampler(sampler: str, ratio: float):
    name = (sampler or "always_on").lower()
    try:
        if name in ("always_on", "alwayson"):
            return sampling.ALWAYS_ON
        if name in ("always_off", "alwaysoff"):
            return sampling.ALWAYS_OFF
        if name in ("traceidratio", "ratio", "parentbased_traceidratio"):
            base = sampling.TraceIdRatioBased(max(0.0, min(1.0, ratio or 1.0)))
            return sampling.ParentBased(base)
    except Exception:
        pass
    return sampling.ALWAYS_ON


def _get_otlp_span_exporter(
    protocol: str = "grpc",
    host: Optional[str] = None,
    port: Optional[int] = None,
    http_encrypted: bool = False,
    agent_auth_token: Optional[str] = None,
):
    """
    Exportador OTLP para spans.
    """
    if protocol.lower() == "grpc":
        endpoint = _compose_grpc_endpoint(host, port)
        headers = _get_otlp_headers(agent_auth_token)
        return OTLPSpanGrpcExporter(endpoint=endpoint, headers=headers, insecure=not http_encrypted)
    elif protocol.lower() == "http":
        endpoint = _compose_http_endpoint(host, port, http_encrypted)
        headers = _get_otlp_headers(agent_auth_token)
        return OTLPSpanHttpExporter(endpoint=endpoint, headers=headers)
    else:
        raise ValueError("Protocolo OTLP inválido: use 'grpc' ou 'http'")


def _compose_grpc_endpoint(host: Optional[str], port: Optional[int]):
    if not host or not port:
        raise ValueError("Host e port são obrigatórios para OTLP gRPC exporter")
    endpoint = f"{host}:{port}"
    logger.info("Endpoint OTLP gRPC: %s", endpoint)
    return endpoint


def _compose_http_endpoint(host: Optional[str], port: Optional[int], encrypted: bool = False):
    if not host or not port:
        raise ValueError("Host e port são obrigatórios para OTLP HTTP exporter")
    scheme = "https" if encrypted else "http"
    endpoint = f"{scheme}://{host}:{port}"
    endpoint = _append_trace_path(endpoint=endpoint)
    logger.info("Endpoint OTLP HTTP: %s", endpoint)
    return endpoint


def _get_otlp_headers(agent_auth_token: Optional[str]) -> Optional[Dict[str, str]]:
    if agent_auth_token:
        headers = {'Authorization': f'Api-Token {agent_auth_token}'}
        logger.info("Headers OTLP: %s", headers)
        return headers
    return None
