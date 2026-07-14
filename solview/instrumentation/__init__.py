"""
solview.instrumentation

Módulo de instrumentação customizada combinando OpenTelemetry tracing e métricas Prometheus.
Fornece decoradores para instrumentar Kafka, HTTP clients, Redis, RabbitMQ e operações de negócio.
"""

from .kafka import (
    kafka_producer_instrumentation,
    kafka_consumer_instrumentation,
)
from .http import http_client_instrumentation
from .business import business_operation_instrumentation
from .redis import redis_client_instrumentation
from .rabbitmq import (
    rabbitmq_publisher_instrumentation,
    rabbitmq_consumer_instrumentation,
)
from .script import script_job_instrumentation

__all__ = [
    "kafka_producer_instrumentation",
    "kafka_consumer_instrumentation",
    "http_client_instrumentation",
    "business_operation_instrumentation",
    "redis_client_instrumentation",
    "rabbitmq_publisher_instrumentation",
    "rabbitmq_consumer_instrumentation",
    "script_job_instrumentation",
]
