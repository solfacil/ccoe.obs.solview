# 📊 Best Practices - Solview

## 🎯 Visão Geral

Este documento apresenta as **melhores práticas** para implementação, configuração e operação do Solview em ambientes empresariais.

---

## 🏗️ Práticas de Instrumentação

### ✅ **DO - Faça Assim**

#### **1. Instrumentação Consistente**

```python
# ✅ BOM: Setup centralizado
from solview import SolviewSettings, setup_logger, setup_tracer
from solview.metrics import SolviewPrometheusMiddleware, prometheus_metrics_response

def create_app() -> FastAPI:
    # Configuração centralizada
    settings = SolviewSettings()
    
    app = FastAPI(
        title=settings.service_name,
        version=settings.service_version
    )
    
    # Setup obrigatório em ordem
    setup_logger(settings)
    setup_tracer(settings, app)
    app.add_middleware(SolviewPrometheusMiddleware, settings=settings)
    app.add_route("/metrics", prometheus_metrics_response)
    
    return app
```

#### **2. Nomeação Consistente de Serviços**

```python
# ✅ BOM: Nomes padronizados
SOLVIEW_SERVICE_NAME=payment-api       # kebab-case
SOLVIEW_SERVICE_NAME=user-management   # consistente
SOLVIEW_SERVICE_NAME=order-processor   # descritivo

# ✅ BOM: Versionamento semântico
SOLVIEW_SERVICE_VERSION=1.2.3
SOLVIEW_SERVICE_VERSION=2.0.0-beta.1
```

#### **3. Logs Estruturados Informativos**

```python
# ✅ BOM: Logs com contexto rico
logger.info(
    "Payment processed successfully",
    payment_id=payment.id,
    amount=payment.amount,
    currency=payment.currency,
    gateway="stripe",
    processing_time_ms=157,
    user_id=payment.user_id
)

# ✅ BOM: Logs de erro detalhados
logger.error(
    "Payment failed",
    payment_id=payment.id,
    error_type="gateway_error",
    error_code="card_declined",
    retry_count=attempt,
    user_id=payment.user_id
)
```

#### **4. Métricas de Negócio**

```python
# ✅ BOM: Métricas específicas do domínio
from prometheus_client import Counter, Histogram

# Business metrics
payments_processed = Counter(
    'payments_processed_total',
    'Total payments processed',
    ['gateway', 'currency', 'status']
)

order_value = Histogram(
    'order_value_amount',
    'Order values',
    ['currency'],
    buckets=[10, 50, 100, 500, 1000, 5000, 10000]
)

# Uso
payments_processed.labels(
    gateway='stripe',
    currency='BRL',
    status='success'
).inc()
```

#### **5. Traces com Contexto**

```python
# ✅ BOM: Spans informativos
with tracer.start_as_current_span("process_payment") as span:
    span.set_attribute("payment.id", payment_id)
    span.set_attribute("payment.amount", amount)
    span.set_attribute("payment.gateway", "stripe")
    span.set_attribute("user.id", user_id)
    
    try:
        result = await payment_gateway.process(payment)
        span.set_attribute("transaction.id", result.transaction_id)
        span.set_status(trace.Status(trace.StatusCode.OK))
        return result
    except Exception as e:
        span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
        span.set_attribute("error.type", type(e).__name__)
        raise
```

### ❌ **DON'T - Evite Fazer**

#### **1. Instrumentação Inconsistente**

```python
# ❌ RUIM: Setup bagunçado
app = FastAPI()
setup_tracer(settings, app)  # Ordem errada
logger = get_logger()        # Sem setup
# Esqueceu middleware e metrics endpoint
```

#### **2. Logs Não Estruturados**

```python
# ❌ RUIM: Logs pouco informativos
logger.info("Payment done")  # Sem contexto
print(f"Error: {e}")         # Não estruturado
logger.debug("Processing")   # Sem informações úteis
```

#### **3. Métricas Excessivas**

```python
# ❌ RUIM: Muitas labels → cardinalidade alta
requests_counter = Counter(
    'requests_total',
    'Requests',
    ['method', 'endpoint', 'status', 'user_id', 'ip', 'user_agent']  # Muitas labels!
)
```

#### **4. Spans Desnecessários**

```python
# ❌ RUIM: Spans demais
with tracer.start_as_current_span("validate_input"):  # Muito granular
    if not input.is_valid():
        with tracer.start_as_current_span("log_error"):  # Desnecessário
            logger.error("Invalid input")
```

---

## 📊 Práticas de Configuração

### ✅ **Configuração por Ambiente**

#### **Desenvolvimento**
```python
# config/development.py
SOLVIEW_SETTINGS = {
    "environment": "development",
    "log_level": "DEBUG",
    "trace_sampling_rate": 1.0,        # 100% para debug
    "enable_data_masking": False,      # Dados visíveis
    "metrics_enabled": True,
    "export_traces": True,
}
```

#### **Staging**
```python
# config/staging.py
SOLVIEW_SETTINGS = {
    "environment": "staging",
    "log_level": "INFO",
    "trace_sampling_rate": 0.5,        # 50% para performance
    "enable_data_masking": True,       # Simular produção
    "metrics_enabled": True
}
```

#### **Produção**
```python
# config/production.py
SOLVIEW_SETTINGS = {
    "environment": "production",
    "log_level": "INFO",
    "trace_sampling_rate": 0.05,       # 5% para performance
    "enable_data_masking": True,       # Compliance obrigatório
    "metrics_enabled": True
}
```

### ✅ **Sampling Strategies**

```python
# Sampling baseado em contexto
class BusinessAwareSampler:
    def should_sample(self, trace_id: str, span_name: str, attributes: dict) -> bool:
        # Sempre sampliar erros
        if attributes.get("error") == "true":
            return True
        
        # Sampling reduzido para health checks
        if span_name in ["/health", "/metrics", "/ready"]:
            return trace_id.endswith("0")  # 1 em 16
        
        # Sampling alto para operações críticas
        if span_name.startswith("payment_") or span_name.startswith("order_"):
            return trace_id.endswith(("0", "1", "2", "3"))  # 1 em 4
        
        # Sampling padrão
        return trace_id.endswith("0")  # 1 em 16
```

---

## 🔒 Práticas de Masking

### ✅ **Data Masking Adequado**

```python
# ✅ BOM: Configuração de masking completa
masking_config = MaskingConfig(
    sensitive_fields=[
        "password", "token", "secret", "key", "authorization",
        "credit_card", "card_number", "cvv", "card_exp",
        "cpf", "rg", "passport", "social_security",
        "bank_account", "routing_number"
    ],
    pii_fields=[
        "email", "phone", "address", "birth_date", "full_name",
        "mother_name", "ip_address", "device_id"
    ],
    custom_patterns={
        "credit_card": r"\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b",
        "cpf": r"\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b",
        "phone": r"\b\(?\d{2}\)?\s?9?\d{4}-?\d{4}\b"
    }
)
```

### ✅ **Logs com Masking**

```python
# ✅ BOM: Nunca logar dados sensíveis
@app.post("/users")
async def create_user(user: UserRequest):
    # Criar cópia sem dados sensíveis para log
    user_for_log = {
        "email": mask_email(user.email),
        "phone": mask_phone(user.phone),
        "document_type": user.document_type,
        # Não incluir: password, document_number, etc.
    }
    
    logger.info("Creating user", user_data=user_for_log)
```

### ✅ **Traces sem PII**

```python
# ✅ BOM: Attributes sem dados sensíveis
with tracer.start_as_current_span("create_user") as span:
    span.set_attribute("user.email_domain", user.email.split("@")[1])
    span.set_attribute("user.document_type", user.document_type)
    span.set_attribute("user.age_range", get_age_range(user.birth_date))
    # Não incluir: email completo, CPF, senha, etc.
```

---

## 📈 Práticas de Performance

### ✅ **Otimização de Métricas**

```python
# ✅ BOM: Labels com cardinalidade controlada
http_requests = Counter(
    'http_requests_total',
    'HTTP requests',
    ['method', 'endpoint_pattern', 'status_class']  # Máximo 5 labels
)

# endpoint_pattern em vez de endpoint específico
# /users/123 → /users/{id}
# status_class em vez de status específico  
# 404 → 4xx
```

### ✅ **Batching Eficiente**

```python
# ✅ BOM: Configuração otimizada para produção
settings = SolviewSettings(
    # Batching agressivo para performance
    span_export_batch_size=1024,       # Padrão: 512
    span_export_timeout_ms=30000,      # Padrão: 30s
    span_export_max_queue_size=4096,   # Padrão: 2048
    
    # Sampling otimizado
    trace_sampling_rate=0.05,          # 5% em produção
    
    # Limites de spans
    max_span_attributes=32,             # Padrão: 128
    max_span_events=32,                 # Padrão: 128
)
```

### ✅ **Async Processing**

```python
# ✅ BOM: Não bloquear requests com observabilidade
async def process_order(order: Order):
    # Instrumentação síncrona rápida
    with tracer.start_as_current_span("process_order") as span:
        span.set_attribute("order.id", order.id)
        
        # Processamento async não bloqueia
        result = await heavy_processing(order)
        
        # Log async se necessário
        asyncio.create_task(
            log_order_metrics(order, result)
        )
        
        return result
```

---

## 🔧 Práticas de Operação

### ✅ **Monitoring e Alerting**

```yaml
# ✅ BOM: Alerts baseados em SLIs
groups:
  - name: sli.rules
    rules:
      # SLI: Availability
      - alert: ServiceAvailabilityLow
        expr: |
          (
            sum(rate(http_responses_total{status_code!~"5.."}[5m])) /
            sum(rate(http_responses_total[5m]))
          ) < 0.995  # 99.5% SLO
        for: 2m
        
      # SLI: Latency
      - alert: ServiceLatencyHigh
        expr: |
          histogram_quantile(0.95, 
            sum(rate(http_request_duration_seconds_bucket[5m])) by (le)
          ) > 0.5  # 500ms SLO
        for: 5m
        
      # SLI: Error Rate
      - alert: ServiceErrorRateHigh
        expr: |
          sum(rate(http_responses_total{status_code=~"5.."}[5m])) /
          sum(rate(http_responses_total[5m])) > 0.01  # 1% error budget
        for: 1m
```

### ✅ **Dashboards Padronizados**

```json
{
  "dashboard": {
    "title": "Service Overview - ${service_name}",
    "tags": ["solview", "overview"],
    "panels": [
      {
        "title": "SLI - Request Rate",
        "targets": [
          {
            "expr": "sum(rate(http_requests_total{service_name=\"$service\"}[5m]))",
            "legendFormat": "Requests/sec"
          }
        ]
      },
      {
        "title": "SLI - Error Rate", 
        "targets": [
          {
            "expr": "sum(rate(http_responses_total{service_name=\"$service\",status_code=~\"5..\"}[5m])) / sum(rate(http_responses_total{service_name=\"$service\"}[5m])) * 100",
            "legendFormat": "Error %"
          }
        ],
        "thresholds": [0.1, 1, 5]
      },
      {
        "title": "SLI - Latency P95",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket{service_name=\"$service\"}[5m])) by (le))",
            "legendFormat": "P95 Latency"
          }
        ]
      }
    ]
  }
}
```

### ✅ **Runbooks**

```markdown
# Runbook: High Error Rate Alert

## Alert: ServiceErrorRateHigh

### Description
Error rate above 1% for more than 1 minute

### Impact
- Users experiencing failures
- SLO at risk
- Potential revenue impact

### Investigation Steps
1. Check service dashboard
2. Look at error traces in Tempo
3. Check recent deployments
4. Verify dependencies status

### Mitigation
1. If recent deployment → rollback
2. If dependency issue → scale up or failover
3. If traffic spike → scale horizontally

### Escalation
- L1: Check dashboard and recent changes
- L2: Deep dive into traces and logs  
- L3: Code-level investigation
```

---

## 📚 Práticas de Documentação

### ✅ **Documentação de Métricas**

```python
# ✅ BOM: Métricas bem documentadas
class BusinessMetrics:
    """
    Business-specific metrics for the payment service.
    
    Metrics:
        payments_processed_total: Total number of payments processed
            Labels: gateway, currency, status
            
        payment_amount_histogram: Distribution of payment amounts  
            Labels: currency
            Buckets: [10, 50, 100, 500, 1000, 5000, 10000]
            
        payment_processing_duration: Time to process payments
            Labels: gateway
            
    Usage:
        payments_processed.labels(gateway='stripe', currency='BRL', status='success').inc()
        payment_amount.labels(currency='BRL').observe(299.90)
    """
```

### ✅ **Guias de Troubleshooting**

```markdown
## Troubleshooting Common Issues

### Metrics not appearing
1. Check /metrics endpoint returns data
2. Verify Prometheus scraping configuration
3. Check service discovery labels

### Traces not correlating
1. Verify trace headers propagation
2. Check OTLP endpoint connectivity
3. Validate service.name consistency

### High cardinality warnings
1. Review metric labels
2. Use label aggregation
3. Consider metric redesign
```

---

## 🎯 Métricas de Qualidade

### ✅ **KPIs de Observabilidade**

```promql
# Coverage: % de endpoints instrumentados
(count(count by (endpoint) (http_requests_total)) / count(count by (endpoint) (nginx_requests_total))) * 100

# Signal-to-Noise: Logs úteis vs total
(count(rate(log_entries{level!="debug"}[5m])) / count(rate(log_entries[5m]))) * 100

# Trace Coverage: % de requests trackeados  
(sum(rate(traces_received_total[5m])) / sum(rate(http_requests_total[5m]))) * 100

# Error Signal Quality: % de erros capturados
(count(rate(log_entries{level="error"}[5m])) / count(rate(http_responses_total{status_code=~"5.."}[5m]))) * 100
```

### ✅ **SLOs de Observabilidade**

| Métrica | SLO | Medição |
|---------|-----|---------|
| **Metrics Availability** | 99.9% | Prometheus uptime |
| **Trace Sampling Coverage** | 95% | Traces vs requests |
| **Log Delivery** | 99% | Loki ingestion rate |
| **Dashboard Load Time** | < 2s | Grafana performance |
| **Alert False Positive** | < 5% | Alert accuracy |

---

## 🚨 Anti-Patterns

### ❌ **Logging Anti-Patterns**

```python
# ❌ RUIM: Log spam
for item in large_list:
    logger.info(f"Processing {item}")  # Flood nos logs

# ❌ RUIM: Logs síncronos pesados
logger.info("User action", user_data=fetch_full_user_profile(user_id))  # DB call

# ❌ RUIM: Logs duplicados
logger.info("Order created", order_id=order.id)
send_notification("Order created", order_id=order.id)  # Log duplicado
```

### ❌ **Metrics Anti-Patterns**

```python
# ❌ RUIM: High cardinality
user_requests = Counter('requests_by_user', ['user_id'])  # Milhões de users

# ❌ RUIM: Métricas temporárias
debug_counter = Counter('debug_xyz_temp')  # Esqueceu de remover

# ❌ RUIM: Labels inconsistentes  
requests_counter.labels(method='GET', endpoint='/users')
requests_counter.labels(http_method='POST', url='/orders')  # Inconsistente
```

### ❌ **Tracing Anti-Patterns**

```python
# ❌ RUIM: Spans demais
with tracer.start_as_current_span("function"):
    with tracer.start_as_current_span("validate"):
        with tracer.start_as_current_span("check_not_null"):  # Muito granular
            if value is None:
                raise ValueError()

# ❌ RUIM: Spans sem contexto
with tracer.start_as_current_span("process"):  # Nome genérico
    # Sem attributes
    do_something()
```

---

## 🎓 Treinamento e Adoção

### ✅ **Onboarding Checklist**

- [ ] Setup de desenvolvimento local
- [ ] Instrumentação básica da primeira API
- [ ] Configuração de dashboards
- [ ] Treinamento em troubleshooting
- [ ] Review de código com foco em observabilidade
- [ ] Certificação em práticas Solview

### ✅ **Code Review Guidelines**

```markdown
## Observability Code Review Checklist

### Setup
- [ ] Solview setup seguindo padrão da empresa
- [ ] Configurações por ambiente  
- [ ] Middleware em ordem correta

### Logging
- [ ] Logs estruturados com contexto suficiente
- [ ] Sem dados sensíveis
- [ ] Níveis apropriados (INFO/ERROR/DEBUG)

### Metrics  
- [ ] Labels com cardinalidade controlada
- [ ] Nomes padronizados
- [ ] Business metrics quando aplicável

### Tracing
- [ ] Spans informativos com attributes
- [ ] Operações críticas trackeadas
- [ ] Sem over-instrumentation
```

---

<div align="center">

**📊 Observabilidade de qualidade começa com boas práticas**

[🏠 Home](../README.md) | [📚 Docs](README.md) | [📋 Instrumentação](instrumentation-guide.md)

</div>
