import logging
from prometheus_client import Counter, Gauge, Histogram

# Logger próprio caso queira logs de instrumentação/erros de métricas
_logger = logging.getLogger("solview.metrics")

METRIC_INFO = Gauge(
    'fastapi_app_info',
    'Application information.',
    ['service_name'],
)

METRIC_REQUESTS = Counter(
    'fastapi_requests_total',
    'Total HTTP requests by method and path.',
    ['method', 'path', 'service_name'],
)

METRIC_RESPONSES = Counter(
    'fastapi_responses_total',
    'HTTP responses by method, path and status code.',
    ['method', 'path', 'status_code', 'service_name'],
)

METRIC_REQUESTS_PROCESSING_TIME = Histogram(
    'fastapi_request_duration_seconds',
    'Histogram of request processing time (seconds).',
    ['method', 'path', 'service_name'],
)

METRIC_EXCEPTIONS = Counter(
    'fastapi_exceptions_total',
    'Count of exceptions raised by method, path, and exception type.',
    ['method', 'path', 'exception_type', 'service_name'],
)

METRIC_REQUESTS_IN_PROGRESS = Gauge(
    'fastapi_requests_in_progress',
    'Number of requests by method and path in progress.',
    ['method', 'path', 'service_name'],
)