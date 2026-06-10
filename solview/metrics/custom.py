"""
Custom metrics for Kafka, HTTP client, Redis, and business operations instrumentation.
"""

from prometheus_client import Counter
from prometheus_client import Histogram
from prometheus_client import Gauge
from prometheus_client import Info

# =============================================================================
# Worker Lifecycle Metrics
#
# Estas métricas não existiam antes. Sem elas, você sabe QUANTO o worker
# processou, mas não sabe SE ele ainda está processando.
# =============================================================================

WORKER_UP = Gauge(
    "worker_up",
    "1 se o worker está rodando, 0 se parou. Útil pra alertas do tipo "
    "'worker morreu silenciosamente'.",
    ["app_name"],
)

WORKER_INFO = Info(
    "worker",
    "Metadata estática do worker (versão, nome do serviço). "
    "Aparece no Grafana pra correlacionar deploys com mudanças de comportamento.",
)

WORKER_READY = Gauge(
    "worker_ready",
    "1 quando o consumer Kafka está conectado e consumindo. "
    "Diferente de worker_up: o processo pode estar vivo mas o consumer travado.",
    ["app_name"],
)


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
        1024,  # 1 KB
        10240,  # 10 KB
        102400,  # 100 KB
        1048576,  # 1 MB
        10485760,  # 10 MB
        104857600,  # 100 MB
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
    buckets=[
        0.001,
        0.005,
        0.01,
        0.025,
        0.05,
        0.1,
        0.25,
        0.5,
        1.0,
        2.5,
        5.0,
        10.0,
        15.0,
        30.0,
        60.0,
        120.0,
        300.0,
    ],
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
        1024,  # 1 KB
        10240,  # 10 KB
        102400,  # 100 KB
        1048576,  # 1 MB
        10485760,  # 10 MB
        104857600,  # 100 MB
        1073741824,  # 1 GB
    ],
)

# --- Consumer: Métricas de resiliência ---

KAFKA_CONSUMER_LAST_SUCCESS_TIMESTAMP = Gauge(
    "kafka_consumer_last_success_timestamp",
    "Unix timestamp da última mensagem processada com sucesso. "
    "Alerta: time() - esta_metrica > 300 significa 5 min sem processar nada.",
    ["topic", "app_name"],
)

KAFKA_CONSUMER_CONSECUTIVE_ERRORS = Gauge(
    "kafka_consumer_consecutive_errors",
    "Número de erros consecutivos sem um sucesso no meio. "
    "Reseta pra 0 a cada sucesso. Diferente do errors_total (que só sobe), "
    "este mostra se o worker está num loop de falha AGORA.",
    ["topic", "app_name"],
)

KAFKA_CONSUMER_LAG = Gauge(
    "kafka_consumer_lag",
    "Consumer lag por tópico e partição. Mostra quantas mensagens estão "
    "pendentes. Se só cresce, o worker não está dando conta.",
    ["topic", "partition", "app_name"],
)

KAFKA_CONSUMER_REBALANCES_TOTAL = Counter(
    "kafka_consumer_rebalances_total",
    "Total de rebalances do consumer group. Rebalances frequentes indicam "
    "instabilidade — pods reiniciando, timeouts, ou consumers lentos.",
    ["app_name"],
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
    buckets=[
        0.005,
        0.01,
        0.025,
        0.05,
        0.1,
        0.25,
        0.5,
        1.0,
        2.5,
        5.0,
        10.0,
        15.0,
        30.0,
        60.0,
        120.0,
        300.0,
    ],
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
        1024,  # 1 KB
        10240,  # 10 KB
        102400,  # 100 KB
        1048576,  # 1 MB
        10485760,  # 10 MB
        104857600,  # 100 MB
        1073741824,  # 1 GB
    ],
)

# =============================================================================
# Redis Client Metrics
# =============================================================================

REDIS_OPERATIONS_TOTAL = Counter(
    "redis_operations_total",
    "Total number of Redis operations executed.",
    ["command", "app_name", "status"],
)

REDIS_OPERATIONS_DURATION_SECONDS = Histogram(
    "redis_operations_duration_seconds",
    "Duration of Redis operations in seconds.",
    ["command", "app_name", "status"],
    buckets=[0.0005, 0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0],
)

REDIS_OPERATIONS_ERRORS_TOTAL = Counter(
    "redis_operations_errors_total",
    "Total number of Redis operation errors.",
    ["command", "error_type", "app_name"],
)

REDIS_OPERATIONS_MEMORY_SAMPLES_TOTAL = Counter(
    "redis_operations_memory_samples_total",
    "Total number of memory samples taken for Redis operations.",
    ["command", "app_name"],
)

REDIS_OPERATIONS_MEMORY_BYTES = Histogram(
    "redis_operations_memory_bytes",
    "Memory usage of Redis operations in bytes.",
    ["command", "app_name", "status"],
    buckets=[
        1024,  # 1 KB
        10240,  # 10 KB
        102400,  # 100 KB
        1048576,  # 1 MB
        10485760,  # 10 MB
        104857600,  # 100 MB
        1073741824,  # 1 GB
    ],
)

# =============================================================================
# RabbitMQ Producer Metrics
# =============================================================================

RABBITMQ_MESSAGES_PUBLISHED_TOTAL = Counter(
    "rabbitmq_messages_published_total",
    "Total number of RabbitMQ messages published.",
    ["routing_key", "exchange", "app_name"],
)

RABBITMQ_PUBLISHER_DURATION_SECONDS = Histogram(
    "rabbitmq_publisher_duration_seconds",
    "Duration of RabbitMQ publisher operations in seconds.",
    ["routing_key", "exchange", "app_name", "status"],
    buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0],
)

RABBITMQ_PUBLISHER_MEMORY_SAMPLES_TOTAL = Counter(
    "rabbitmq_publisher_memory_samples_total",
    "Total number of memory samples taken for RabbitMQ publisher operations.",
    ["routing_key", "exchange", "app_name"],
)

RABBITMQ_PUBLISHER_ERRORS_TOTAL = Counter(
    "rabbitmq_publisher_errors_total",
    "Total number of RabbitMQ publisher errors.",
    ["routing_key", "exchange", "error_type", "app_name"],
)

RABBITMQ_PUBLISHER_MEMORY_BYTES = Histogram(
    "rabbitmq_publisher_memory_bytes",
    "Memory usage of RabbitMQ publisher operations in bytes.",
    ["routing_key", "exchange", "app_name", "status"],
    buckets=[
        1024,  # 1 KB
        10240,  # 10 KB
        102400,  # 100 KB
        1048576,  # 1 MB
        10485760,  # 10 MB
        104857600,  # 100 MB
        1073741824,  # 1 GB
    ],
)

# =============================================================================
# RabbitMQ Consumer Metrics
# =============================================================================

RABBITMQ_MESSAGES_CONSUMED_TOTAL = Counter(
    "rabbitmq_messages_consumed_total",
    "Total number of RabbitMQ messages consumed.",
    ["queue", "app_name"],
)

RABBITMQ_CONSUMER_PROCESSING_DURATION_SECONDS = Histogram(
    "rabbitmq_consumer_processing_duration_seconds",
    "Duration of RabbitMQ message processing in seconds.",
    ["queue", "handler", "app_name", "status"],
    buckets=[
        0.001,
        0.005,
        0.01,
        0.025,
        0.05,
        0.1,
        0.25,
        0.5,
        1.0,
        2.5,
        5.0,
        10.0,
        15.0,
        30.0,
        60.0,
        120.0,
        300.0,
        600.0,
        800.0,
    ],
)

RABBITMQ_CONSUMER_MEMORY_SAMPLES_TOTAL = Counter(
    "rabbitmq_consumer_memory_samples_total",
    "Total number of memory samples taken for RabbitMQ consumer operations.",
    ["queue", "handler", "app_name"],
)

RABBITMQ_CONSUMER_ERRORS_TOTAL = Counter(
    "rabbitmq_consumer_errors_total",
    "Total number of RabbitMQ consumer errors.",
    ["queue", "error_type", "app_name"],
)

RABBITMQ_CONSUMER_MEMORY_BYTES = Histogram(
    "rabbitmq_consumer_memory_bytes",
    "Memory usage of RabbitMQ consumer operations in bytes.",
    ["queue", "handler", "app_name", "status"],
    buckets=[
        1024,  # 1 KB
        10240,  # 10 KB
        102400,  # 100 KB
        1048576,  # 1 MB
        10485760,  # 10 MB
        104857600,  # 100 MB
        1073741824,  # 1 GB
    ],
)

# --- Consumer: Métricas de resiliência ---

RABBITMQ_CONSUMER_LAST_SUCCESS_TIMESTAMP = Gauge(
    "rabbitmq_consumer_last_success_timestamp",
    "Unix timestamp da última mensagem processada com sucesso. "
    "Alerta: time() - esta_metrica > 300 significa 5 min sem processar nada.",
    ["queue", "app_name"],
)

RABBITMQ_CONSUMER_CONSECUTIVE_ERRORS = Gauge(
    "rabbitmq_consumer_consecutive_errors",
    "Número de erros consecutivos sem um sucesso no meio. "
    "Reseta pra 0 a cada sucesso. Diferente do errors_total (que só sobe), "
    "este mostra se o worker está num loop de falha AGORA.",
    ["queue", "app_name"],
)

RABBITMQ_CONSUMER_UNACKED_MESSAGES = Gauge(
    "rabbitmq_consumer_unacked_messages",
    "Mensagens não confirmadas (unacked) por fila. "
    "Equivalente ao consumer lag do Kafka — valores altos indicam "
    "que o consumer não está acompanhando a taxa de produção.",
    ["queue", "app_name"],
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
    buckets=[
        0.001,
        0.005,
        0.01,
        0.025,
        0.05,
        0.1,
        0.25,
        0.5,
        1.0,
        2.5,
        5.0,
        10.0,
        15.0,
        30.0,
        60.0,
        120.0,
        300.0,
    ],
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
        1024,  # 1 KB
        10240,  # 10 KB
        102400,  # 100 KB
        1048576,  # 1 MB
        10485760,  # 10 MB
        104857600,  # 100 MB
        1073741824,  # 1 GB
    ],
)

# =============================================================================
# Script / Cronjob Metrics
#
# Scripts e cronjobs são processos de curta duração que não servem um endpoint
# HTTP persistente. As métricas abaixo são exportadas via Pushgateway.
# =============================================================================

SCRIPT_RUNS_TOTAL = Counter(
    "script_runs_total",
    "Total de execuções do script/cronjob por status (success|error). "
    "Use para calcular taxa de falha: rate(script_runs_total{status='error'}[5m]).",
    ["job_name", "app_name", "status"],
)

SCRIPT_DURATION_SECONDS = Histogram(
    "script_duration_seconds",
    "Duração total da execução do script em segundos. "
    "Buckets cobrem desde scripts rápidos (1s) até jobs longos (2h).",
    ["job_name", "app_name", "status"],
    buckets=[
        1.0,     # 1 s
        5.0,     # 5 s
        15.0,    # 15 s
        30.0,    # 30 s
        60.0,    # 1 min
        120.0,   # 2 min
        300.0,   # 5 min
        600.0,   # 10 min
        1800.0,  # 30 min
        3600.0,  # 1 h
        7200.0,  # 2 h
    ],
)

SCRIPT_LAST_SUCCESS_TIMESTAMP = Gauge(
    "script_last_success_timestamp",
    "Unix timestamp da última execução bem-sucedida do script. "
    "Alerta: time() - esta_metrica > <intervalo_esperado> indica job parado.",
    ["job_name", "app_name"],
)

SCRIPT_LAST_RUN_TIMESTAMP = Gauge(
    "script_last_run_timestamp",
    "Unix timestamp da última execução do script (independente de sucesso ou erro). "
    "Útil para detectar job que nem chegou a iniciar.",
    ["job_name", "app_name"],
)

SCRIPT_MEMORY_SAMPLES_TOTAL = Counter(
    "script_memory_samples_total",
    "Total de amostras de memória coletadas para scripts.",
    ["job_name", "app_name"],
)

SCRIPT_MEMORY_BYTES = Histogram(
    "script_memory_bytes",
    "Uso de memória de scripts em bytes.",
    ["job_name", "app_name", "status"],
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
