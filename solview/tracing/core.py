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
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.trace import set_tracer_provider
from opentelemetry.util.http.httplib import HttpClientInstrumentor
from solview.settings import SolviewSettings

settings = SolviewSettings()
logger = logging.getLogger("solview.tracing.core")

def parse_otlp_endpoint_and_protocol(
    endpoint: Optional[str] = None,
    protocol: Optional[str] = None,
    http_encrypted: Optional[bool] = None
) -> (str, int, str, bool):
    """
    Lê e interpreta endpoint e protocolo OTLP conforme padrão OpenTelemetry.
    """
    endpoint = endpoint or os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "localhost:4317")
    protocol = (protocol or os.getenv("OTEL_EXPORTER_OTLP_PROTOCOL", "grpc")).lower()
    http_encrypted = (
        http_encrypted
        if http_encrypted is not None
        else os.getenv("OTEL_EXPORTER_OTLP_HTTP_ENCRYPTED", "false").lower() == "true"
    )

    # Default values
    host = "localhost"
    port = 4317

    # Remove prefix se houver (grpc://, http://, https://)
    if "://" in endpoint:
        scheme, endpoint = endpoint.split("://", 1)
        # Se preferir, sobrescreva protocolo pelo scheme
        if scheme == "https":
            protocol = "http"
            http_encrypted = True
        elif scheme == "http":
            protocol = "http"
            http_encrypted = False
        elif scheme == "grpc":
            protocol = "grpc"
    if ":" in endpoint:
        host, port_str = endpoint.rsplit(":", 1)
        try:
            port = int(port_str)
        except Exception:
            raise ValueError(f"Porta inválida no OTLP endpoint: {endpoint}")
    else:
        host = endpoint

    return host, port, protocol, http_encrypted

def setup_tracer(
    app: FastAPI,
    service_name: Optional[str] = None,
    service_version: Optional[str] = None,
    deployment_name: Optional[str] = None,
    otlp_exporter_protocol: Optional[str] = None,
    otlp_exporter_endpoint: Optional[str] = None,
    otlp_exporter_http_encrypted: Optional[bool] = None,
    otlp_agent_auth_token: Optional[str] = None,
    otlp_sqlalchemy_enable_commenter: Optional[bool] = None,
    use_console_exporter_on_unittest: bool = True,
) -> TracerProvider:
    """
    Setup universal do Tracer OpenTelemetry (FastAPI/Solview).
    Todos parâmetros são opcionais e podem ser sobrescritos por ENV padrão OpenTelemetry.
    """
    # Lê padrões se não preenchidos
    service_name = service_name or getattr(settings, "service_name_composed", "app")
    service_version = service_version or getattr(settings, "version", "1.0.0")
    deployment_name = deployment_name or getattr(settings, "environment", None)
    otlp_agent_auth_token = otlp_agent_auth_token or os.getenv("OTEL_EXPORTER_OTLP_AUTH_TOKEN")
    otlp_sqlalchemy_enable_commenter = (
        otlp_sqlalchemy_enable_commenter
        if otlp_sqlalchemy_enable_commenter is not None
        else os.getenv("OTEL_SQLALCHEMY_ENABLE_COMMENTER", "false").lower() == "true"
    )

    # Lê endpoint e protocolo da OpenTelemetry, permite override manual
    host, port, protocol, http_encrypted = parse_otlp_endpoint_and_protocol(
        endpoint=otlp_exporter_endpoint,
        protocol=otlp_exporter_protocol,
        http_encrypted=otlp_exporter_http_encrypted,
    )

    resource = _get_resource(service_name, service_version, deployment_name)
    tracer_provider = TracerProvider(sampler=sampling.ALWAYS_ON, resource=resource)
    set_tracer_provider(tracer_provider)
    logger.info("TracerProvider configurado | Serviço: %s v%s", service_name, service_version)

    python_env = os.getenv("PYTHON_ENV", "")
    if use_console_exporter_on_unittest and python_env == "unittest":
        tracer_provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))
        logger.info("[solview.tracing] Modo unittest: ConsoleSpanExporter habilitado.")
        return tracer_provider

    # Instrumentação automática
    LoggingInstrumentor().instrument(tracer_provider=tracer_provider, set_logging_format=True)
    HTTPXClientInstrumentor().instrument(tracer_provider=tracer_provider)
    AsyncPGInstrumentor().instrument(tracer_provider=tracer_provider)
    SQLAlchemyInstrumentor().instrument(
        tracer_provider=tracer_provider,
        enable_commenter=otlp_sqlalchemy_enable_commenter,
        commenter_options={},
    )
    HttpClientInstrumentor().instrument(tracer_provider=tracer_provider)
    if app:
        FastAPIInstrumentor().instrument_app(app=app, tracer_provider=tracer_provider)
        logger.info("[solview.tracing] FastAPI instrumentada para tracing.")

    exporter = _get_otlp_span_exporter(
        protocol=protocol,
        host=host,
        port=port,
        http_encrypted=http_encrypted,
        agent_auth_token=otlp_agent_auth_token,
    )
    tracer_provider.add_span_processor(BatchSpanProcessor(exporter))
    logger.info("[solview.tracing] Exportador OTLP conectado: %s://%s:%s", protocol, host, port)
    return tracer_provider

def _get_resource(service_name: str, service_version: str, deployment_name: Optional[str]) -> Resource:
    attrs = {SERVICE_NAME: service_name, SERVICE_VERSION: service_version}
    if deployment_name:
        attrs["deployment_name"] = deployment_name
    logger.info("[solview.tracing] Resource OTEL: %s", attrs)
    return Resource.create(attrs)

def _get_otlp_span_exporter(
    protocol: str = "grpc",
    host: Optional[str] = None,
    port: Optional[int] = None,
    http_encrypted: bool = False,
    agent_auth_token: Optional[str] = None,
):
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