"""
Custom metrics for Kafka, HTTP client, and business operations instrumentation.
"""

from prometheus_client import Counter, Histogram

# =============================================================================
# Kafka Producer Metrics
# =============================================================================

KAFKA_MESSAGES_PRODUCED_TOTAL = Counter(
    "kafka_messages_produced_total",
    "Total number of Kafka messages produced.",
    ["topic", "app_name"],
)

KAFKA_PRODUCER_DURATION_SECONDS = Histogram(
    "kafka_producer_duration_seconds",
    "Duration of Kafka producer operations in seconds.",
    ["topic", "app_name", "status"],
    buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0],
)

KAFKA_PRODUCER_MEMORY_SAMPLES_TOTAL = Counter(
    "kafka_producer_memory_samples_total",
    "Total number of memory samples taken for Kafka producer operations.",
    ["topic", "app_name"],
)

KAFKA_PRODUCER_ERRORS_TOTAL = Counter(
    "kafka_producer_errors_total",
    "Total number of Kafka producer errors.",
    ["topic", "error_type", "app_name"],
)

KAFKA_PRODUCER_MEMORY_BYTES = Histogram(
    "kafka_producer_memory_bytes",
    "Memory usage of Kafka producer operations in bytes.",
    ["topic", "app_name", "status"],
    buckets=[
        1024,        # 1 KB
        10240,       # 10 KB
        102400,      # 100 KB
        1048576,     # 1 MB
        10485760,    # 10 MB
        104857600,   # 100 MB
        1073741824,  # 1 GB
    ],
)

# =============================================================================
# Kafka Consumer Metrics
# =============================================================================

KAFKA_MESSAGES_CONSUMED_TOTAL = Counter(
    "kafka_messages_consumed_total",
    "Total number of Kafka messages consumed.",
    ["topic", "app_name"],
)

KAFKA_MESSAGE_PROCESSING_DURATION_SECONDS = Histogram(
    "kafka_message_processing_duration_seconds",
    "Duration of Kafka message processing in seconds.",
    ["topic", "handler", "app_name", "status"],
    buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
)

KAFKA_CONSUMER_MEMORY_SAMPLES_TOTAL = Counter(
    "kafka_consumer_memory_samples_total",
    "Total number of memory samples taken for Kafka consumer operations.",
    ["topic", "handler", "app_name"],
)

KAFKA_CONSUMER_ERRORS_TOTAL = Counter(
    "kafka_consumer_errors_total",
    "Total number of Kafka consumer errors.",
    ["topic", "error_type", "app_name"],
)

KAFKA_CONSUMER_MEMORY_BYTES = Histogram(
    "kafka_consumer_memory_bytes",
    "Memory usage of Kafka consumer operations in bytes.",
    ["topic", "handler", "app_name", "status"],
    buckets=[
        1024,        # 1 KB
        10240,       # 10 KB
        102400,      # 100 KB
        1048576,     # 1 MB
        10485760,    # 10 MB
        104857600,   # 100 MB
        1073741824,  # 1 GB
    ],
)

# =============================================================================
# HTTP Client Metrics
# =============================================================================

HTTP_OUTGOING_REQUESTS_TOTAL = Counter(
    "http_outgoing_requests_total",
    "Total number of outgoing HTTP requests.",
    ["method", "status_code", "url_host", "url_path", "app_name", "status"],
)

HTTP_OUTGOING_REQUESTS_DURATION_SECONDS = Histogram(
    "http_outgoing_requests_duration_seconds",
    "Duration of outgoing HTTP requests in seconds.",
    ["method", "url_host", "url_path", "app_name", "status"],
    buckets=[0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
)

HTTP_OUTGOING_REQUESTS_ERRORS_TOTAL = Counter(
    "http_outgoing_requests_errors_total",
    "Total number of outgoing HTTP request errors.",
    ["method", "url_host", "url_path", "error_type", "app_name"],
)

HTTP_OUTGOING_REQUESTS_MEMORY_SAMPLES_TOTAL = Counter(
    "http_outgoing_requests_memory_samples_total",
    "Total number of memory samples taken for outgoing HTTP requests.",
    ["method", "url_host", "url_path", "app_name"],
)

HTTP_OUTGOING_REQUESTS_MEMORY_BYTES = Histogram(
    "http_outgoing_requests_memory_bytes",
    "Memory usage of outgoing HTTP requests in bytes.",
    ["method", "url_host", "url_path", "app_name", "status"],
    buckets=[
        1024,        # 1 KB
        10240,       # 10 KB
        102400,      # 100 KB
        1048576,     # 1 MB
        10485760,    # 10 MB
        104857600,   # 100 MB
        1073741824,  # 1 GB
    ],
)

# =============================================================================
# Business Operations Metrics
# =============================================================================

BUSINESS_OPERATIONS_TOTAL = Counter(
    "business_operations_total",
    "Total number of business operations executed.",
    ["operation", "app_name", "status"],
)

BUSINESS_OPERATIONS_DURATION_SECONDS = Histogram(
    "business_operations_duration_seconds",
    "Duration of business operations in seconds.",
    ["operation", "app_name", "status"],
    buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
)

BUSINESS_OPERATIONS_MEMORY_SAMPLES_TOTAL = Counter(
    "business_operations_memory_samples_total",
    "Total number of memory samples taken for business operations.",
    ["operation", "app_name"],
)

BUSINESS_OPERATIONS_MEMORY_BYTES = Histogram(
    "business_operations_memory_bytes",
    "Memory usage of business operations in bytes.",
    ["operation", "app_name", "status"],
    buckets=[
        1024,        # 1 KB
        10240,       # 10 KB
        102400,      # 100 KB
        1048576,     # 1 MB
        10485760,    # 10 MB
        104857600,   # 100 MB
        1073741824,  # 1 GB
    ],
)