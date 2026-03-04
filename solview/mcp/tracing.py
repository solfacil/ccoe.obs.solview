"""OpenTelemetry tracing setup for FastMCP servers.

Provides the same TracerProvider, MeterProvider, OTLP exporter and library-level
auto-instrumentation (httpx, requests, asyncpg, sqlalchemy, redis, logging) that
``solview.tracing.setup_tracer`` offers for FastAPI, but without any
FastAPI / Starlette dependency.
"""

import logging
import os

from opentelemetry.instrumentation.asyncpg import AsyncPGInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.instrumentation.logging import LoggingInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.util.http.httplib import HttpClientInstrumentor
from opentelemetry.exporter.prometheus import PrometheusMetricReader
from opentelemetry.metrics import set_meter_provider
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import (
    BatchSpanProcessor,
    ConsoleSpanExporter,
    SimpleSpanProcessor,
)
from opentelemetry.trace import set_tracer_provider

from solview.config import get_settings
from solview.tracing.core import _get_resource, _get_sampler, _get_otlp_span_exporter

logger = logging.getLogger("solview.mcp.tracing")


def setup_mcp_tracer() -> TracerProvider:
    """
    Setup do OpenTelemetry tracing para servidores FastMCP.

    Configura TracerProvider, MeterProvider (Prometheus) e instrumentação
    automática para bibliotecas usadas dentro de tools MCP:

    - **httpx** (chamadas HTTP async)
    - **requests** (chamadas HTTP sync)
    - **asyncpg** (PostgreSQL async)
    - **sqlalchemy** (ORMs / SQL)
    - **redis** (Redis sync e async)
    - **logging** (correlação trace_id nos logs)
    - **http.client** (stdlib)

    Não instrumenta FastAPI/Starlette — para isso use ``solview.tracing.setup_tracer(app)``.

    Requer ``setup_settings()`` chamado antes.

    Usage::

        from solview import setup_settings, SolviewSettings
        from solview.mcp import SolviewMCPMiddleware, setup_mcp_tracer

        setup_settings(SolviewSettings(service_name="meu-mcp"))
        setup_mcp_tracer()

        mcp = FastMCP("MeuServidor")
        mcp.add_middleware(SolviewMCPMiddleware())

    Returns:
        TracerProvider configurado.
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

    tracer_provider = TracerProvider(
        sampler=_get_sampler(settings.trace_sampler, settings.trace_sampling_ratio),
        resource=resource,
    )
    set_tracer_provider(tracer_provider)
    logger.info(
        "TracerProvider configurado (MCP) | Serviço: %s v%s",
        service_name,
        service_version,
    )

    prometheus_reader = PrometheusMetricReader()
    metrics_provider = MeterProvider(metric_readers=[prometheus_reader])
    set_meter_provider(metrics_provider)
    logger.info(
        "MeterProvider configurado (MCP) | Serviço: %s v%s",
        service_name,
        service_version,
    )

    python_env = os.getenv("PYTHON_ENV", "")
    if (
        getattr(settings, "use_console_exporter_on_unittest", False)
        and python_env == "unittest"
    ):
        tracer_provider.add_span_processor(SimpleSpanProcessor(ConsoleSpanExporter()))
        logger.info(
            "[solview.mcp.tracing] Modo unittest: ConsoleSpanExporter habilitado."
        )
        return tracer_provider

    os.environ.setdefault("OTEL_SEMCONV_STABILITY_OPT_IN", "http")

    LoggingInstrumentor().instrument(set_logging_format=True)
    HTTPXClientInstrumentor().instrument()
    AsyncPGInstrumentor().instrument()
    SQLAlchemyInstrumentor().instrument(
        enable_commenter=settings.otlp_sqlalchemy_enable_commenter,
        commenter_options={},
    )
    HttpClientInstrumentor().instrument()
    RequestsInstrumentor().instrument()
    RedisInstrumentor().instrument()
    logger.info(
        "[solview.mcp.tracing] Instrumentação library-level ativada "
        "(httpx, requests, asyncpg, sqlalchemy, redis, logging, http.client)"
    )

    exporter = _get_otlp_span_exporter(
        protocol=settings.otlp_exporter_protocol,
        host=settings.otlp_exporter_host,
        port=settings.otlp_exporter_port,
        http_encrypted=settings.otlp_exporter_http_encrypted,
        agent_auth_token=settings.otlp_agent_auth_token,
    )
    tracer_provider.add_span_processor(BatchSpanProcessor(exporter))
    logger.info(
        "[solview.mcp.tracing] Exportador OTLP conectado: %s://%s:%s",
        settings.otlp_exporter_protocol,
        settings.otlp_exporter_host,
        settings.otlp_exporter_port,
    )

    return tracer_provider
