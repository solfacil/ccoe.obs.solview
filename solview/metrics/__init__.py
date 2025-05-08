"""
solview.metrics

Módulo universal para coleta de métricas — preparado para uso em web, workers, jobs, e APIs.
- Middleware Prometheus para ASGI (FastAPI, Starlette)
- Exporters e helpers para aplicação universal
"""

from .core import (
    METRIC_INFO,
    METRIC_REQUESTS,
    METRIC_RESPONSES,
    METRIC_REQUESTS_PROCESSING_TIME,
    METRIC_EXCEPTIONS,
    METRIC_REQUESTS_IN_PROGRESS,
)
from .exporters import (
    SolviewPrometheusMiddleware,
    prometheus_metrics_response,
)

__all__ = [
    "SolviewPrometheusMiddleware",
    "prometheus_metrics_response",
    "METRIC_INFO",
    "METRIC_REQUESTS",
    "METRIC_RESPONSES",
    "METRIC_REQUESTS_PROCESSING_TIME",
    "METRIC_EXCEPTIONS",
    "METRIC_REQUESTS_IN_PROGRESS",
]