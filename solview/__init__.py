"""
solview - Observabilidade clara como o Sol ☀️

Biblioteca centralizada de logging, métricas e tracing (Solfácil).
"""

from .settings import SolviewSettings, TracingSettings, MetricsSettings
from .config import get_settings, setup_settings
from .solview_logging import get_logger, setup_logger
from .tracing import get_tracer, setup_tracer
from .instrumentation import (
    kafka_producer_instrumentation,
    kafka_consumer_instrumentation,
    http_client_instrumentation,
    business_operation_instrumentation,
)

__all__ = [
    "SolviewSettings",
    "TracingSettings",
    "MetricsSettings",
    "setup_settings",
    "get_settings",
    "get_logger",
    "get_tracer",
    "setup_tracer",
    "setup_logger",
    "kafka_producer_instrumentation",
    "kafka_consumer_instrumentation",
    "http_client_instrumentation",
    "business_operation_instrumentation",
]
