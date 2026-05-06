import logging
import os
from typing import Any, Optional, Dict
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import (
    OTLPSpanExporter as OTLPSpanGrpcExporter,
)
from opentelemetry.exporter.otlp.proto.http.trace_exporter import (
    OTLPSpanExporter as OTLPSpanHttpExporter,
)
from opentelemetry.exporter.otlp.proto.http.trace_exporter import _append_trace_path
from opentelemetry.instrumentation.asyncpg import AsyncPGInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.instrumentation.logging import LoggingInstrumentor
from opentelemetry.instrumentation.aio_pika import AioPikaInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.sdk.resources import SERVICE_NAME, SERVICE_VERSION, Resource
from opentelemetry.sdk.trace import TracerProvider, sampling
from opentelemetry.semconv.resource import ResourceAttributes
from opentelemetry.sdk.trace.export import (
    BatchSpanProcessor,
    ConsoleSpanExporter,
    SimpleSpanProcessor,
)
from opentelemetry.trace import set_tracer_provider
from opentelemetry.metrics import set_meter_provider
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.exporter.prometheus import PrometheusMetricReader
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.util.http.httplib import HttpClientInstrumentor
from ..config import get_settings

logger = logging.getLogger("solview.tracing.core")

_state: Dict[str, Any] = {
    "tracer_provider_initialized": False,
    "tracer_provider": None,
    "libs_instrumented": False,
    "fastapi_instrumented_apps": set(),
}


def setup_tracer_provider() -> TracerProvider:
    """
    Cria/retorna ``TracerProvider`` + ``MeterProvider`` + Resource + Sampler e
    adiciona o ``BatchSpanProcessor`` com o exportador OTLP.

    Idempotente: chamadas subsequentes retornam o ``TracerProvider`` já criado
    sem registrar processadores duplicados.

    Em modo ``PYTHON_ENV=unittest`` com ``use_console_exporter_on_unittest``,
    adiciona apenas um ``SimpleSpanProcessor(ConsoleSpanExporter())`` e retorna.

    Ordem recomendada de uso para serviços com engine SQLAlchemy criada em
    import-time::

        setup_solview_settings(...)
        setup_tracer_provider()
        setup_tracer_libs()      # ANTES de importar módulos que criam engine
        ... imports do projeto que tocam DB ...

        app = FastAPI(...)
        setup_tracer_fastapi(app)
    """
    if _state["tracer_provider_initialized"] and _state["tracer_provider"] is not None:
        return _state["tracer_provider"]

    settings = get_settings()
    service_name = settings.service_name
    service_version = settings.version
    resource = _get_resource(
        service_name=service_name,
        service_version=service_version,
        deployment_name=settings.environment,
        service_namespace=settings.service_namespace,
    )

    tracer_provider = TracerProvider(
        sampler=_get_sampler(settings.trace_sampler, settings.trace_sampling_ratio),
        resource=resource,
    )
    set_tracer_provider(tracer_provider)
    logger.info(
        "TracerProvider configurado | Serviço: %s v%s", service_name, service_version
    )

    prometheus_reader = PrometheusMetricReader()
    metrics_provider = MeterProvider(metric_readers=[prometheus_reader])
    set_meter_provider(metrics_provider)
    logger.info(
        "MeterProvider configurado | Serviço: %s v%s", service_name, service_version
    )

    python_env = os.getenv("PYTHON_ENV", "")
    if (
        getattr(settings, "use_console_exporter_on_unittest", False)
        and python_env == "unittest"
    ):
        # SimpleSpanProcessor evita flush assíncrono em stdout fechado no teardown do pytest.
        tracer_provider.add_span_processor(SimpleSpanProcessor(ConsoleSpanExporter()))
        logger.info("[solview.tracing] Modo unittest: ConsoleSpanExporter habilitado.")
        _state["tracer_provider"] = tracer_provider
        _state["tracer_provider_initialized"] = True
        return tracer_provider

    exporter = _get_otlp_span_exporter(
        protocol=settings.otlp_exporter_protocol,
        host=settings.otlp_exporter_host,
        port=settings.otlp_exporter_port,
        http_encrypted=settings.otlp_exporter_http_encrypted,
        agent_auth_token=settings.otlp_agent_auth_token,
    )
    tracer_provider.add_span_processor(BatchSpanProcessor(exporter))
    logger.info(
        "[solview.tracing] Exportador OTLP conectado: %s://%s:%s",
        settings.otlp_exporter_protocol,
        settings.otlp_exporter_host,
        settings.otlp_exporter_port,
    )

    _state["tracer_provider"] = tracer_provider
    _state["tracer_provider_initialized"] = True
    return tracer_provider


def setup_tracer_libs() -> None:
    """
    Aplica auto-instrumentações de biblioteca (framework-agnostic):
    Logging, HTTPX, AsyncPG, SQLAlchemy, http.client, Requests, Redis, AioPika.

    Idempotente: chamadas repetidas não re-executam as instrumentações nem
    duplicam logs.

    Deve ser chamada **antes** de qualquer import que crie engine SQLAlchemy
    em nível de módulo, caso contrário a engine pré-existente não recebe os
    event listeners de ``before_cursor_execute``/``after_cursor_execute`` e
    o atributo ``db.statement`` não é populado nos spans.
    """
    if _state["libs_instrumented"]:
        return

    settings = get_settings()
    python_env = os.getenv("PYTHON_ENV", "")
    if (
        getattr(settings, "use_console_exporter_on_unittest", False)
        and python_env == "unittest"
    ):
        # Em modo unittest com console exporter não aplicamos auto-instrumentação
        # de bibliotecas para preservar o comportamento legado de setup_tracer().
        _state["libs_instrumented"] = True
        return

    os.environ.setdefault("OTEL_SEMCONV_STABILITY_OPT_IN", "http")

    LoggingInstrumentor().instrument(set_logging_format=True)
    HTTPXClientInstrumentor().instrument()
    AsyncPGInstrumentor().instrument()
    SQLAlchemyInstrumentor().instrument(
        enable_commenter=settings.otlp_sqlalchemy_enable_commenter, commenter_options={}
    )
    HttpClientInstrumentor().instrument()
    RequestsInstrumentor().instrument()
    RedisInstrumentor().instrument()
    AioPikaInstrumentor().instrument()
    logger.info(
        "[solview.tracing] Instrumentação library-level ativada "
        "(httpx, requests, asyncpg, sqlalchemy, redis, aio-pika, logging, http.client)"
    )

    _state["libs_instrumented"] = True


def setup_tracer_fastapi(app: Any) -> None:
    """
    Aplica instrumentação específica de FastAPI: ``FastAPIInstrumentor`` e
    ``prometheus-fastapi-instrumentator``.

    Idempotente por instância de ``app``: se a mesma app for passada novamente,
    a instrumentação não é re-aplicada.

    Se ``app`` não for uma instância de ``FastAPI`` (ou FastAPI não estiver
    instalado), a chamada é ignorada silenciosamente.
    """
    if app is None:
        return

    try:
        from fastapi import FastAPI as _FastAPI
    except ImportError:
        logger.debug(
            "[solview.tracing] FastAPI não instalado — instrumentação FastAPI ignorada"
        )
        return

    if not isinstance(app, _FastAPI):
        return

    app_id = id(app)
    if app_id in _state["fastapi_instrumented_apps"]:
        return

    from prometheus_fastapi_instrumentator import Instrumentator
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

    Instrumentator().instrument(app=app).expose(app)

    excluded_urls = "/metrics|/ready|/info|/docs|/openapi.json|/favicon.ico"
    FastAPIInstrumentor().instrument_app(
        app=app,
        excluded_urls=excluded_urls,
    )
    logger.info(
        "[solview.tracing] FastAPI instrumentada para tracing "
        "(excluindo URLs de infraestrutura: %s)",
        excluded_urls,
    )

    _state["fastapi_instrumented_apps"].add(app_id)


def setup_tracer(app: Any = None) -> TracerProvider:
    """
    Setup do OpenTelemetry tracing provider e auto-instrumentações de biblioteca.

    Wrapper compatível com a API original — chama, em ordem,
    ``setup_tracer_provider()``, ``setup_tracer_libs()`` e, se ``app`` for uma
    instância de FastAPI, ``setup_tracer_fastapi(app)``.

    Funciona tanto para FastAPI quanto para FastMCP (ou qualquer app Python):
    - Quando ``app`` é uma instância de ``FastAPI``, aplica instrumentação
      específica (FastAPIInstrumentor + prometheus-fastapi-instrumentator).
    - Quando ``app`` é ``None`` (ex.: FastMCP), aplica apenas as instrumentações
      de biblioteca.

    Para resolver o *ordering bug* com engines SQLAlchemy criadas em
    import-time, prefira chamar diretamente ``setup_tracer_provider()`` e
    ``setup_tracer_libs()`` antes dos imports do projeto, e
    ``setup_tracer_fastapi(app)`` depois de criar o ``FastAPI``.
    """
    tracer_provider = setup_tracer_provider()
    setup_tracer_libs()
    if app is not None:
        setup_tracer_fastapi(app)
    return tracer_provider


def setup_tracer_from_env(app: Any = None) -> TracerProvider:
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
        return OTLPSpanGrpcExporter(
            endpoint=endpoint, headers=headers, insecure=not http_encrypted
        )
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


def _compose_http_endpoint(
    host: Optional[str], port: Optional[int], encrypted: bool = False
):
    if not host or not port:
        raise ValueError("Host e port são obrigatórios para OTLP HTTP exporter")
    scheme = "https" if encrypted else "http"
    endpoint = f"{scheme}://{host}:{port}"
    endpoint = _append_trace_path(endpoint=endpoint)
    logger.info("Endpoint OTLP HTTP: %s", endpoint)
    return endpoint


def _get_otlp_headers(agent_auth_token: Optional[str]) -> Optional[Dict[str, str]]:
    if agent_auth_token:
        headers = {"Authorization": f"Api-Token {agent_auth_token}"}
        logger.info("Headers OTLP: %s", headers)
        return headers
    return None
