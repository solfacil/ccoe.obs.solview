# 📋 Guia Completo de Instrumentação Solview

## 🎯 Visão Geral

Este guia mostra como instrumentar qualquer aplicação Python/FastAPI com o **Solview** para observabilidade completa em **menos de 10 minutos**.

---

## 🚀 Instrumentação Rápida (5 minutos)

### 1. **Instalação**

```bash
# Instalar Solview
pip install solview

# Dependências adicionais (se necessário)
pip install opentelemetry-instrumentation-fastapi
pip install opentelemetry-instrumentation-httpx
```

### 2. **Instrumentação Básica**

```python
# main.py
from fastapi import FastAPI
from solview import (
    SolviewSettings,
    setup_logger,
    setup_tracer,
    get_logger,
)
from solview.metrics import (
    SolviewPrometheusMiddleware,
    prometheus_metrics_response
)

# ✅ 1. Configurar settings
settings = SolviewSettings(
    service_name="minha-api",
    service_version="1.0.0",
    environment="production",
    # Automático: detecta variáveis de ambiente
)

# ✅ 2. Criar aplicação
app = FastAPI(
    title="Minha API",
    version="1.0.0"
)

# ✅ 3. Setup de logging estruturado
setup_logger(settings)
logger = get_logger(__name__)

# ✅ 4. Setup de tracing distribuído
setup_tracer(settings, app)

# ✅ 5. Middleware de métricas
app.add_middleware(
    SolviewPrometheusMiddleware,
    settings=settings
)

# ✅ 6. Endpoint de métricas
app.add_route("/metrics", prometheus_metrics_response)

# ✅ 7. Endpoints instrumentados automaticamente
@app.get("/health")
async def health():
    logger.info("Health check called")
    return {"status": "healthy", "service": settings.service_name}

@app.get("/api/users/{user_id}")
async def get_user(user_id: int):
    logger.info("Getting user", user_id=user_id)
    
    # Simulação de busca
    user = {"id": user_id, "name": f"User {user_id}"}
    
    logger.info("User found", user=user, user_id=user_id)
    return user
```

### 3. **Configuração de Ambiente**

```bash
# .env
SERVICE_NAME=minha-api
VERSION=1.0.0
ENVIRONMENT=production
OTLP_EXPORTER_HOST=localhost
LOG_LEVEL=INFO
```

### 4. **Executar**

```bash
# Iniciar aplicação
uvicorn main:app --reload --port 8000

# Testar instrumentação
curl http://localhost:8000/health
curl http://localhost:8000/metrics
curl http://localhost:8000/api/users/123
```

**🎊 Pronto! Sua aplicação agora está 100% instrumentada!**

---

## 🤖 Instrumentação MCP (FastMCP)

Para instrumentar servidores **FastMCP** (v2+), use o módulo `solview.mcp`:

### 1. **Instalação**

```bash
pip install solview[mcp]
```

### 2. **Instrumentação**

```python
from fastmcp import FastMCP
from prometheus_client import start_http_server
from solview import SolviewSettings, setup_settings, setup_logger, setup_tracer
from solview.mcp import SolviewMCPMiddleware, SolviewMCPASGIMiddleware

# Configurar Solview
setup_settings(SolviewSettings(service_name="meu-mcp-server"))
setup_logger()
setup_tracer()

# Expor métricas (MCP não tem /metrics nativo)
start_http_server(port=9090)

# Servidor MCP com observabilidade
mcp = FastMCP("MeuServidor")
mcp.add_middleware(SolviewMCPMiddleware())

@mcp.tool
async def processar_pedido(pedido_id: str) -> str:
    # Automaticamente instrumentado:
    # - Span: mcp.tool.processar_pedido
    # - Métrica: business_operations_total{operation="tool.processar_pedido"}
    return f"Pedido {pedido_id} processado"
```

O `setup_tracer()` sem app ativa as mesmas auto-instrumentações de biblioteca (httpx, asyncpg, sqlalchemy, requests, redis) sem aplicar instrumentação específica de FastAPI.

Para que o trace tenha um span raiz por request (ex.: "POST /mcp") em vez da primeira operação (ex.: Redis SETEX), envolva o app ASGI com `SolviewMCPASGIMiddleware` antes de subir o servidor (ex.: `app = SolviewMCPASGIMiddleware(mcp.get_asgi_app())`). Veja o [Guia MCP completo](mcp.md).

---

## 🔧 Instrumentação Avançada

### 📊 **Métricas Customizadas**

```python
from solview.metrics import get_metrics_registry
from prometheus_client import Counter, Histogram, Gauge

# Obter registry
metrics = get_metrics_registry()

# Métricas customizadas
order_counter = Counter(
    'orders_total',
    'Total orders processed',
    ['status', 'payment_method'],
    registry=metrics
)

processing_time = Histogram(
    'order_processing_seconds',
    'Order processing time',
    ['order_type'],
    registry=metrics
)

active_connections = Gauge(
    'active_connections',
    'Active database connections',
    registry=metrics
)

@app.post("/api/orders")
async def create_order(order: OrderRequest):
    start_time = time.time()
    
    try:
        # Processar pedido
        result = await process_order(order)
        
        # Incrementar contador de sucesso
        order_counter.labels(
            status='success',
            payment_method=order.payment_method
        ).inc()
        
        # Registrar tempo de processamento
        processing_time.labels(
            order_type=order.type
        ).observe(time.time() - start_time)
        
        return result
        
    except Exception as e:
        # Incrementar contador de erro
        order_counter.labels(
            status='error',
            payment_method=order.payment_method
        ).inc()
        
        logger.error("Order processing failed", error=str(e), order_id=order.id)
        raise
```

### 🔍 **Traces Customizados**

```python
from opentelemetry import trace
from solview.tracing import get_tracer

tracer = get_tracer(__name__)

@app.get("/api/complex-operation/{operation_id}")
async def complex_operation(operation_id: str):
    # Span principal da operação
    with tracer.start_as_current_span("complex_operation") as span:
        span.set_attribute("operation.id", operation_id)
        span.set_attribute("operation.type", "data_processing")
        
        # Sub-operação 1: Validação
        with tracer.start_as_current_span("validate_input") as validation_span:
            validation_span.set_attribute("input.size", len(operation_id))
            
            if not operation_id.isalnum():
                validation_span.set_status(trace.Status(trace.StatusCode.ERROR, "Invalid input"))
                raise ValueError("Invalid operation ID")
            
            validation_span.set_status(trace.Status(trace.StatusCode.OK))
        
        # Sub-operação 2: Processamento
        with tracer.start_as_current_span("process_data") as process_span:
            process_span.set_attribute("processing.method", "async")
            
            # Simular processamento
            await asyncio.sleep(0.1)
            result = f"Processed: {operation_id}"
            
            process_span.set_attribute("result.size", len(result))
            process_span.set_status(trace.Status(trace.StatusCode.OK))
        
        # Sub-operação 3: Persistência
        with tracer.start_as_current_span("save_result") as save_span:
            save_span.set_attribute("storage.type", "database")
            
            # Simular save
            logger.info("Saving result", operation_id=operation_id, result=result)
            
            save_span.set_status(trace.Status(trace.StatusCode.OK))
        
        span.set_status(trace.Status(trace.StatusCode.OK))
        return {"operation_id": operation_id, "result": result}
```

### 📝 **Logging Estruturado Avançado**

```python
from solview import get_logger

# Logger com contexto
logger = get_logger(__name__)

@app.post("/api/payments")
async def process_payment(payment: PaymentRequest):
    # Context logging
    with logger.bind(
        payment_id=payment.id,
        amount=payment.amount,
        currency=payment.currency,
        user_id=payment.user_id
    ) as payment_logger:
        
        payment_logger.info("Payment processing started")
        
        try:
            # Validação
            payment_logger.debug("Validating payment data")
            if payment.amount <= 0:
                payment_logger.warning("Invalid payment amount", amount=payment.amount)
                raise ValueError("Amount must be positive")
            
            # Processamento
            payment_logger.info("Processing payment with gateway")
            result = await payment_gateway.process(payment)
            
            # Log com dados estruturados
            payment_logger.info(
                "Payment processed successfully",
                transaction_id=result.transaction_id,
                gateway_response_time=result.response_time,
                fees=result.fees
            )
            
            return result
            
        except PaymentGatewayError as e:
            payment_logger.error(
                "Payment gateway error",
                error_code=e.code,
                gateway_message=e.message,
                retry_after=e.retry_after
            )
            raise
            
        except Exception as e:
            payment_logger.error(
                "Unexpected payment error",
                error_type=type(e).__name__,
                error_message=str(e)
            )
            raise
```

---

## 🛡️ Segurança e Masking

### 🔒 **Masking Automático**

```python
from solview.security import MaskingConfig

# Configurar masking
masking_config = MaskingConfig(
    sensitive_fields=[
        "password", "token", "secret", "key",
        "cpf", "rg", "credit_card", "account_number"
    ],
    pii_fields=[
        "email", "phone", "address", "birth_date"
    ],
    custom_patterns={
        "credit_card": r"\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}",
        "cpf": r"\d{3}\.?\d{3}\.?\d{3}-?\d{2}"
    }
)

# Aplicar no settings
settings = SolviewSettings(
    service_name="secure-api",
    enable_data_masking=True,
    masking_config=masking_config
)

@app.post("/api/users")
async def create_user(user: UserRequest):
    # Dados sensíveis são automaticamente mascarados nos logs
    logger.info("Creating user", user_data=user.dict())
    
    # CPF será logado como "***.***.***-**"
    # Email será logado como "u****@****.com"
    # Password não aparecerá nos logs
    
    return await user_service.create(user)
```

---

## 🌐 Instrumentação para Chamadas HTTP

### 📡 **Clientes HTTP**

```python
import httpx
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor

# Instrumentar HTTPX automaticamente
HTTPXClientInstrumentor().instrument()

class ExternalAPIClient:
    def __init__(self):
        self.client = httpx.AsyncClient(
            base_url="https://api.externa.com",
            timeout=30.0
        )
        self.logger = get_logger(__name__)
    
    async def get_user_data(self, user_id: str):
        with tracer.start_as_current_span("external_api_call") as span:
            span.set_attribute("external.service", "user-service")
            span.set_attribute("user.id", user_id)
            
            try:
                self.logger.info("Calling external API", user_id=user_id)
                
                response = await self.client.get(f"/users/{user_id}")
                response.raise_for_status()
                
                data = response.json()
                
                span.set_attribute("response.size", len(response.content))
                span.set_status(trace.Status(trace.StatusCode.OK))
                
                self.logger.info(
                    "External API call successful",
                    user_id=user_id,
                    response_time=response.elapsed.total_seconds()
                )
                
                return data
                
            except httpx.HTTPError as e:
                span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
                
                self.logger.error(
                    "External API call failed",
                    user_id=user_id,
                    error=str(e),
                    status_code=getattr(e.response, 'status_code', None)
                )
                raise
```

---

## 🔴 Instrumentação Redis

Para instrumentação manual de operações Redis com métricas Prometheus, use o decorator `redis_client_instrumentation`:

```python
from solview import redis_client_instrumentation

@redis_client_instrumentation(command="get")
async def get_cache(key: str) -> str | None:
    return await redis_client.get(key)

@redis_client_instrumentation(command="set")
async def set_cache(key: str, value: str, ttl: int = 300):
    await redis_client.set(key, value, ex=ttl)
```

O decorator registra métricas `redis_operations_*` (total, duração, erros, memória). A auto-instrumentação via `setup_tracer()` já rastreia operações Redis com OpenTelemetry (tanto `redis` sync quanto `redis.asyncio` async).

---

## 🗄️ Instrumentação de Banco de Dados

### 🐘 **PostgreSQL com SQLAlchemy**

```python
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor

# Instrumentar SQLAlchemy
SQLAlchemyInstrumentor().instrument()

# Configurar engine
engine = create_async_engine(
    "postgresql+asyncpg://user:pass@localhost/db",
    echo=False,  # Não fazer echo SQL (já capturado por tracing)
    pool_size=20,
    max_overflow=30
)

AsyncSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

class UserRepository:
    def __init__(self):
        self.logger = get_logger(__name__)
    
    async def get_user(self, user_id: int):
        with tracer.start_as_current_span("db_get_user") as span:
            span.set_attribute("db.operation", "SELECT")
            span.set_attribute("db.table", "users")
            span.set_attribute("user.id", user_id)
            
            async with AsyncSessionLocal() as session:
                try:
                    self.logger.debug("Querying user from database", user_id=user_id)
                    
                    # Query será automaticamente trackeada
                    result = await session.get(User, user_id)
                    
                    if result:
                        span.set_attribute("db.rows_affected", 1)
                        self.logger.info("User found", user_id=user_id)
                    else:
                        span.set_attribute("db.rows_affected", 0)
                        self.logger.warning("User not found", user_id=user_id)
                    
                    span.set_status(trace.Status(trace.StatusCode.OK))
                    return result
                    
                except Exception as e:
                    span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
                    self.logger.error("Database error", user_id=user_id, error=str(e))
                    raise
```

---

## 🔧 Configurações por Ambiente

### 🏠 **Desenvolvimento**

```python
# config/development.py
from solview import SolviewSettings
from solview.settings import TracingSettings

settings = SolviewSettings(
    service_name="minha-api-dev",
    environment="development",
    log_level="DEBUG",
    otlp_exporter_host="localhost",
    ignore_mask=True,  # Masking desabilitado em dev
    enable_memory_profiling=True,
    sampling_memory_profiling=1.0,
)
```

### 🧪 **Staging**

```python
# config/staging.py
from solview import SolviewSettings
from solview.settings import TracingSettings

settings = SolviewSettings(
    service_name="minha-api-staging",
    environment="staging",
    log_level="INFO",
    otlp_exporter_host="otel-collector.staging",
    trace_sampling_ratio=0.1,  # 10% de sampling
    enable_memory_profiling=True,
    sampling_memory_profiling=0.1,
)
```

### 🚀 **Produção**

```python
# config/production.py
from solview import SolviewSettings
from solview.settings import TracingSettings

settings = SolviewSettings(
    service_name="minha-api",
    environment="production",
    log_level="INFO",
    otlp_exporter_host="otel-collector.prod",
    trace_sampling_ratio=0.05,  # 5% de sampling para performance
    enable_memory_profiling=True,
    sampling_memory_profiling=0.01,
)
```

---

## 📊 Validação da Instrumentação

### ✅ **Checklist de Instrumentação**

```bash
# 1. Verificar métricas
curl http://localhost:8000/metrics | grep -E "(http_requests_total|http_request_duration)"

# 2. Verificar logs estruturados
# Logs devem aparecer em JSON com trace_id

# 3. Verificar traces
# Acessar Grafana -> Explore -> Tempo

# 4. Verificar correlação
# Clicar em trace -> "Related Logs" -> "Request Rate"
```

### 🧪 **Teste Automatizado**

```python
# test_instrumentation.py
import pytest
from fastapi.testclient import TestClient
from prometheus_client import REGISTRY

def test_metrics_endpoint():
    with TestClient(app) as client:
        response = client.get("/metrics")
        assert response.status_code == 200
        assert "http_requests_total" in response.text

def test_logging_structured():
    with TestClient(app) as client:
        response = client.get("/health")
        # Verificar se logs contém trace_id e campos estruturados

def test_tracing_headers():
    with TestClient(app) as client:
        response = client.get("/health")
        # Verificar se response contém headers de tracing
        assert "traceparent" in response.headers
```

---

## 🚨 Troubleshooting

### ❌ **Problemas Comuns**

#### **1. Métricas não aparecem**
```bash
# Verificar endpoint
curl http://localhost:8000/metrics

# Verificar Prometheus
curl http://localhost:9090/api/v1/targets
```

#### **2. Traces não aparecem**
```bash
# Verificar OTLP endpoint
curl http://localhost:4317/v1/traces

# Verificar variáveis de ambiente
env | grep OTEL
```

#### **3. Logs não estruturados**
```python
# Verificar setup do logger
from solview import get_logger
logger = get_logger(__name__)
logger.info("Test", key="value")  # Deve gerar JSON
```

#### **4. Correlação não funciona**
- Verificar se traces estão sendo gerados
- Verificar configuração do Grafana datasource
- Verificar se métricas têm labels corretos

---

## 🎯 Próximos Passos

### 📈 **Evolução da Instrumentação**

1. **Semana 1**: Instrumentação básica (este guia)
2. **Semana 2**: Métricas customizadas de negócio
3. **Semana 3**: Dashboards específicos da aplicação
4. **Semana 4**: Alerting e SLOs

### 📚 **Leitura Recomendada**

- [📊 Guia de Métricas](metrics.md) - Métricas disponíveis
- [🔍 Guia de Tracing](tracing.md) - Traces distribuídos
- [📝 Guia de Logging](logging.md) - Logs estruturados
- [🤖 Guia MCP](mcp.md) - Observabilidade para FastMCP
 

---

<div align="center">

**🎊 Parabéns! Sua aplicação está totalmente instrumentada com Solview!**

[🏠 Home](../README.md) | [📚 Docs](README.md) | [🚀 Quick Start](../README.md#-quick-start)

</div>
