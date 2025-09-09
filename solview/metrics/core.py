import logging
from prometheus_client import Counter, Gauge, Histogram

# Logger próprio caso queira logs de instrumentação/erros de métricas
_logger = logging.getLogger("solview.metrics")

# ✅ Métricas HTTP universais compatíveis com OpenTelemetry e Grafana Service Graph
METRIC_INFO = Gauge(
    'http_app_info',
    'Application information.',
    ['service_name'],
)

METRIC_REQUESTS = Counter(
    'http_requests_total',
    'Total HTTP requests by method and path.',
    ['method', 'path', 'service_name'],
)

METRIC_RESPONSES = Counter(
    'http_responses_total',
    'HTTP responses by method, path and status code.',
    ['method', 'path', 'status_code', 'service_name'],
)

METRIC_REQUESTS_PROCESSING_TIME = Histogram(
    'http_request_duration_seconds',
    'Histogram of request processing time (seconds).',
    ['method', 'path', 'service_name'],
)

METRIC_EXCEPTIONS = Counter(
    'http_exceptions_total',
    'Count of exceptions raised by method, path, and exception type.',
    ['method', 'path', 'exception_type', 'service_name'],
)

METRIC_REQUESTS_IN_PROGRESS = Gauge(
    'http_requests_in_progress',
    'Number of requests by method and path in progress.',
    ['method', 'path', 'service_name'],
)