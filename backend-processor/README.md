# 🔧 Backend Processor - Service Graph Generator

## 📋 Visão Geral

O **Backend Processor** é uma aplicação secundária desenvolvida especificamente para demonstrar comunicação entre serviços e gerar **service graphs** ricos no Grafana. Esta aplicação se comunica com a Demo App principal através de HTTP, criando traces distribuídos que resultam em visualizações detalhadas de dependências entre serviços.

## 🏗️ Arquitetura

### Padrão de Comunicação
```
┌─────────────────────┐    HTTP/REST   ┌─────────────────────┐
│   Backend Processor │ ──────────────► │    Demo App         │
│   (Port 8001)       │                 │    (Port 8000)      │
│                     │                 │                     │
│ - Analytics         │                 │ - Products API      │
│ - Processing        │                 │ - Orders API        │
│ - Batch Operations  │                 │ - Health Checks     │
└─────────────────────┘                 └─────────────────────┘
            │                                      │
            └──── OpenTelemetry Traces ────────────┘
                         │
                         ▼
                ┌─────────────────────┐
                │  OTLP Collector     │
                │  (Service Graph)    │
                └─────────────────────┘
```

## 🚀 Funcionalidades

### 📊 Analytics Endpoints
- **GET** `/api/v1/analytics/products` - Análise de produtos
- **GET** `/api/v1/analytics/orders` - Análise de pedidos
- **GET** `/api/v1/analytics/report` - Relatório do sistema completo
- **POST** `/api/v1/analytics/process-batch` - Processamento em lote

### ⚙️ Processing Endpoints
- **POST** `/api/v1/processor/orders/process` - Workflow de processamento de pedidos
- **POST** `/api/v1/processor/products/enrich` - Enriquecimento de produtos
- **GET** `/api/v1/processor/jobs/{job_id}` - Status de jobs
- **GET** `/api/v1/processor/jobs` - Lista de jobs

### ❤️ Health Endpoints
- **GET** `/health` - Health check com verificação de dependências
- **GET** `/ready` - Readiness check para Kubernetes
- **GET** `/info` - Informações detalhadas da aplicação

## 🔍 Service Graph Features

### Tipos de Chamadas Demonstradas

1. **Chamadas Simples**: Analytics básicos
2. **Chamadas Paralelas**: Enriquecimento de produtos
3. **Workflows Complexos**: Processamento de pedidos com múltiplas etapas
4. **Processamento em Lote**: Múltiplas chamadas sequenciais
5. **Background Tasks**: Jobs assíncronos

### Traces Gerados

- `analytics_analyze_products` → `demo_app_get_products`
- `analytics_analyze_orders` → `demo_app_get_orders`
- `processor_order_workflow` → `demo_app_create_order`
- `processor_enrich_products` → `demo_app_get_product` (paralelo)
- `analytics_generate_system_report` → múltiplas chamadas Demo App

## 🛠️ Configuração

### Variáveis de Ambiente

```bash
# Service Configuration
SERVICE_NAME=backend-processor
SERVICE_VERSION=1.0.0
ENVIRONMENT=development
PORT=8001

# Demo App Integration
DEMO_APP_URL=http://solview-demo:8000
DEMO_APP_TIMEOUT=30

# OpenTelemetry (Production Ready)
OTEL_ENABLED=true
OTEL_SERVICE_NAME=backend-processor
OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector:4317
OTEL_RESOURCE_ATTRIBUTES=service.name=backend-processor,service.version=1.0.0

# Processing Configuration
BATCH_SIZE=10
PROCESSING_INTERVAL_SECONDS=30
RETRY_ATTEMPTS=3
```

## 🐳 Docker Deployment

### Build da Aplicação
```bash
# Build da imagem
docker build -f backend-processor/Dockerfile -t backend-processor:latest .

# Executar via Docker Compose
docker-compose up backend-processor
```

### Multi-stage Build
- **Stage 1**: Builder com dependências de compilação
- **Stage 2**: Runtime otimizado com usuário não-root
- **Health Check**: Verificação automática de saúde

## 📊 Observabilidade

### Solview Integration
```python
# Configuração automática do Solview
solview_settings = SolviewSettings(
    service_name="backend-processor",
    version="1.0.0",
    environment="development",
    otlp_exporter_host="otel-collector",
    otlp_exporter_port=4317
)

# Features habilitadas
- setup_logger(solview_settings)      # Logging estruturado
- SolviewPrometheusMiddleware          # Métricas automáticas
- setup_tracer()                       # Tracing distribuído
```

### Métricas Prometheus
- **Endpoint**: `http://localhost:8001/metrics`
- **Job Name**: `backend-processor`
- **Scrape Interval**: 15s

### Logging Estruturado
```json
{
  "level": "INFO",
  "timestamp": "2024-01-15T10:30:00Z",
  "service": "backend-processor",
  "trace_id": "abc123...",
  "span_id": "def456...",
  "event": "demo_app_get_products",
  "products_count": 25,
  "processing_time_ms": 145
}
```

## 🧪 Testando Service Graph

### Script Automatizado
```bash
# Executar script de teste
./scripts/test-service-graph.sh
```

### Teste Manual
```bash
# 1. Analytics de produtos
curl "http://localhost:8001/api/v1/analytics/products"

# 2. Processamento de pedido
curl -X POST "http://localhost:8001/api/v1/processor/orders/process" \
  -H "Content-Type: application/json" \
  -d '{"cart_id": "cart-001", "customer_email": "test@example.com"}'

# 3. Enriquecimento de produtos (paralelo)
curl -X POST "http://localhost:8001/api/v1/processor/products/enrich" \
  -H "Content-Type: application/json" \
  -d '{"product_ids": ["prod-001", "prod-002"], "enrichment_type": "full"}'
```

## 📈 Visualização no Grafana

### Service Graph Dashboard
1. Abrir Grafana: `http://localhost:3000`
2. Navigate: **Explore** → **Tempo**
3. Query: `{service.name="backend-processor"}`
4. Visualizar **Service Graph** tab

### Traces Esperados
```
backend-processor
    ├── analytics_analyze_products
    │   └── demo_app_get_products
    ├── processor_order_workflow
    │   ├── demo_app_create_order
    │   └── demo_app_get_product
    └── analytics_generate_system_report
        ├── demo_app_check_health
        ├── demo_app_get_products
        └── demo_app_get_orders
```

## 🔧 Desenvolvimento

### Estrutura do Projeto
```
backend-processor/
├── src/
│   └── app/
│       ├── api/              # REST endpoints
│       │   ├── analytics.py  # Analytics operations
│       │   ├── processor.py  # Processing workflows
│       │   └── health.py     # Health checks
│       ├── services/         # External services
│       │   └── demo_client.py # Demo App HTTP client
│       ├── environment.py    # Configuration
│       └── server.py         # FastAPI application
├── requirements.txt          # Python dependencies
├── Dockerfile               # Production container
└── README.md               # This file
```

### Dependencies
- **FastAPI**: Web framework
- **httpx**: Async HTTP client
- **OpenTelemetry**: Tracing instrumentation
- **Solview**: Observability integration
- **Pydantic**: Data validation

## 🚀 Production Readiness

### Security Features
- Non-root container user
- Health checks configurados
- CORS configurado
- Input validation com Pydantic

### Performance Features
- Async/await em todas as operações
- Connection pooling (httpx)
- Parallel processing where applicable
- Graceful shutdown

### Monitoring Features
- Health checks com dependency verification
- Structured logging
- Distributed tracing
- Prometheus metrics
- Error tracking

## 📚 Exemplos de Uso

### Analytics Workflow
```python
# 1. Backend Processor recebe request
# 2. Faz chamada para Demo App /products
# 3. Processa dados localmente
# 4. Retorna analytics agregados
# 5. Trace completo fica visível no Grafana
```

### Order Processing Workflow
```python
# 1. Recebe request de processamento
# 2. Cria pedido na Demo App
# 3. Busca detalhes dos produtos
# 4. Enriquece dados do pedido
# 5. Agenda notificação (background task)
# 6. Service graph mostra todas as interações
```

## 🎯 Objetivos do Service Graph

1. **Demonstrar Microservices Communication**
2. **Visualizar Dependencies entre serviços**
3. **Identificar Performance bottlenecks**
4. **Monitorar Error rates entre serviços**
5. **Validar Distributed tracing setup**

---

## 🔗 Links Relacionados

- [Demo App](../demo-app/README.md)
- [Docker Compose](../docker-compose.yml)
- [Grafana Dashboards](../docker/grafana/)
- [Service Graph Tests](../scripts/test-service-graph.sh)
