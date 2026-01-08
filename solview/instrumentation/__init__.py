"""
solview.instrumentation

Módulo de instrumentação customizada combinando OpenTelemetry tracing e métricas Prometheus.
Fornece decoradores para instrumentar Kafka, HTTP clients e operações de negócio.
"""

from .kafka import (
    kafka_producer_instrumentation,
    kafka_consumer_instrumentation,
)
from .http import http_client_instrumentation
from .business import business_operation_instrumentation

__all__ = [
    "kafka_producer_instrumentation",
    "kafka_consumer_instrumentation",
    "http_client_instrumentation",
    "business_operation_instrumentation",
]

