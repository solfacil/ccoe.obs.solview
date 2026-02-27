"""
solview - Observabilidade clara como o Sol ☀️

Biblioteca centralizada de logging, métricas e tracing (Solfácil).
"""

from .settings import SolviewSettings, TracingSettings, MetricsSettings
from .config import setup_solview
from .solview_logging import get_logger
from .tracing import get_tracer
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
    "setup_solview",
    "get_settings",
    "get_logger",
    "get_tracer",
    "kafka_producer_instrumentation",
    "kafka_consumer_instrumentation",
    "http_client_instrumentation",
    "business_operation_instrumentation",
]
