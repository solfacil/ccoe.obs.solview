# 🐳 Solview Docker Compose Stack

Stack completa **LGTM** (Loki, Grafana, Tempo, Mimir/Prometheus) + OpenTelemetry Collector para testar o Solview localmente.

---

## 🚀 Quick Start

### **1. Pré-requisitos**
```bash
# Docker e Docker Compose
docker --version
docker-compose --version

# Pelo menos 4GB RAM livres
# Portas disponíveis: 3000, 3100, 3200, 4317, 4318, 6379, 8000, 9090
```

### **2. Executar a Stack**
```bash
# Clone o projeto (se ainda não fez)
git clone <repo-url>
cd ccoe.obs.solview

# Subir toda a stack
docker-compose up -d

# Verificar se todos os serviços subiram
docker-compose ps

# Acompanhar logs
docker-compose logs -f solview-demo
```

### **3. Acessar as Interfaces**

| Serviço | URL | Credenciais |
|---------|-----|-------------|
| 🌟 **Demo App** | http://localhost:8000 | N/A |
| 📊 **Grafana** | http://localhost:3000 | admin / solview123 |
| 📈 **Prometheus** | http://localhost:9090 | N/A |
| 📝 **Loki** | http://localhost:3100 | N/A |
| 🔍 **Tempo** | http://localhost:3200 | N/A |
| 🛰️ **OTEL Collector** | http://localhost:13133/health | N/A |

---

## 🎯 **Demo Scenarios**

### **Scenario 1: Basic Observability**
```bash
# 1. Acessar a demo app
curl http://localhost:8000/

# 2. Gerar algumas requisições
curl -X POST http://localhost:8000/demo/process-data \
  -H "Content-Type: application/json" \
  -d '{"cpf": "12345678909", "email": "user@example.com"}'

# 3. Verificar métricas (precisa de API key)
curl -H "X-API-Key: sk-demo-1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef" \
  http://localhost:8000/metrics

# 4. Ver no Grafana
# - Ir para http://localhost:3000
# - Login: admin / solview123
# - Dashboard: "Solview - Observabilidade Aplicações"
```

### **Scenario 2: Security Features**
```bash
# 1. Testar masking de dados
curl -X POST http://localhost:8000/demo/process-data \
  -H "Content-Type: application/json" \
  -d '{"cpf": "12345678909", "credit_card": "1234 5678 9012 3456", "email": "sensitive@data.com"}'

# 2. Testar endpoint sem autenticação (deve falhar)
curl http://localhost:8000/metrics
# Expected: HTTP 401

# 3. Testar admin endpoint sem JWT (deve falhar)
curl http://localhost:8000/admin/config
# Expected: HTTP 401

# 4. Verificar logs de auditoria no Loki
# - Grafana → Explore → Loki
# - Query: {service_name="solview-demo"} |= "authentication_failure"
```

### **Scenario 3: Load Testing & Alerts**
```bash
# 1. Gerar carga sintética
curl http://localhost:8000/demo/generate-load?count=50

# 2. Simular erros
for i in {1..10}; do curl http://localhost:8000/demo/simulate-errors; done

# 3. Simular requisições lentas
curl http://localhost:8000/demo/slow-request

# 4. Verificar alertas no Prometheus
# - http://localhost:9090/alerts
# - Procurar por "HighAuthenticationFailures", "SuspiciousActivity"
```

### **Scenario 4: Distributed Tracing**
```bash
# 1. Fazer requisições que geram traces
curl -X POST http://localhost:8000/demo/process-data \
  -H "Content-Type: application/json" \
  -d '{"user_id": "user123", "operation": "complex_processing"}'

# 2. Ver traces no Grafana
# - Grafana → Explore → Tempo
# - Search por service: solview-demo
# - Ver trace completo com spans

# 3. Correlation entre logs e traces
# - No Loki, procurar por trace_id
# - Clicar no trace_id para ir ao Tempo
```

---

## 🔧 **Configuration Details**

### **Environment Variables (Demo App)**
```env
# Solview Core
SOLVIEW_LOG_LEVEL=INFO
SOLVIEW_ENVIRONMENT=development
SOLVIEW_SERVICE_NAME=solview-demo
SOLVIEW_VERSION=2.0.0

# OpenTelemetry
OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector:4317
OTEL_EXPORTER_OTLP_AUTH_TOKEN=demo-token-12345

# Security (para demo)
SOLVIEW_API_KEY=sk-demo-1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef
SOLVIEW_JWT_SECRET=jwt-demo-secret-1234567890abcdef1234567890abcdef1234567890abcdef123
```

### **Prometheus Scrape Config**
```yaml
# Scrape da demo app com autenticação
- job_name: 'solview-demo'
  static_configs:
    - targets: ['solview-demo:8000']
  authorization:
    credentials: 'sk-demo-1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef'
```

### **Data Flow**
```
App → OTEL Collector → {Prometheus, Loki, Tempo} ← Grafana
```

---

## 📊 **Pre-configured Dashboards**

### **1. Solview Overview Dashboard**
- **Request Rate & Error Rate** por serviço
- **Response Time P95** com thresholds
- **Error Rate por Status Code**
- **Response Time Distribution** (heatmap)
- **Exceptions por Tipo** (pie chart)
- **Top Endpoints** por request rate
- **Trace Samples** (últimos traces)

### **2. Security Dashboard**
- **Authentication Failures** por tempo
- **Rate Limit Violations**
- **Security Events** por tipo
- **Suspicious Activity** patterns

### **3. Infrastructure Dashboard**
- **OTEL Collector** health
- **Prometheus** targets
- **Loki** ingestion rate
- **Tempo** trace rate

---

## 🚨 **Pre-configured Alerts**

### **Security Alerts**
- `HighAuthenticationFailures`: > 5 falhas/min
- `SuspiciousActivity`: > 10 requests 400/min
- `RateLimitViolations`: > 1 request 429/min

### **Performance Alerts**
- `HighResponseTime`: P95 > 2s por 5min
- `HighErrorRate`: > 5% de erros 5xx por 2min

### **Availability Alerts**
- `SolviewServiceDown`: serviço inacessível por 1min
- `OTELCollectorDown`: collector down por 1min

---

## 🛠️ **Troubleshooting**

### **Service Not Starting**
```bash
# Verificar logs
docker-compose logs <service-name>

# Verificar portas em uso
netstat -tulpn | grep :3000

# Restart de serviço específico
docker-compose restart grafana
```

### **No Metrics Appearing**
```bash
# Verificar targets no Prometheus
# http://localhost:9090/targets

# Verificar logs do OTEL Collector
docker-compose logs otel-collector

# Testar endpoint de métricas manualmente
curl -H "X-API-Key: sk-demo-..." http://localhost:8000/metrics
```

### **No Logs in Loki**
```bash
# Verificar logs do Loki
docker-compose logs loki

# Verificar configuração do OTEL Collector
docker exec solview-otel-collector cat /etc/otel-collector-config.yaml

# Testar ingestion diretamente
curl -X POST http://localhost:3100/loki/api/v1/push
```

### **No Traces in Tempo**
```bash
# Verificar logs do Tempo
docker-compose logs tempo

# Verificar se app está enviando traces
curl http://localhost:8000/demo/process-data # Gerar trace

# Verificar no Grafana Explore → Tempo
```

---

## 🧪 **Advanced Testing**

### **Custom Alerts Testing**
```bash
# Script para testar alertas
./scripts/test-alerts.sh

# Ou manualmente:
# Gerar muitos erros 401
for i in {1..20}; do curl http://localhost:8000/metrics; done

# Gerar muitos erros 400
for i in {1..30}; do curl -X POST http://localhost:8000/demo/process-data -d "invalid"; done
```

### **Performance Testing**
```bash
# Com wrk (se instalado)
wrk -t12 -c400 -d30s http://localhost:8000/

# Com curl simples
seq 1 100 | xargs -I {} -P 10 curl http://localhost:8000/demo/slow-request
```

### **Security Testing**
```bash
# Testar input validation
curl -X POST http://localhost:8000/demo/process-data \
  -H "Content-Type: application/json" \
  -d '{"data": "<script>alert(\"xss\")</script>"}'

# Testar masking compliance
curl -X POST http://localhost:8000/demo/process-data \
  -H "Content-Type: application/json" \
  -d '{"cpf": "12345678909", "cc": "1234-5678-9012-3456"}'
```

---

## 🗂️ **Data Persistence**

### **Volumes Created**
- `prometheus_data`: Métricas (retention: 15 dias)
- `grafana_data`: Dashboards e configurações
- `loki_data`: Logs (retention: configurável)
- `tempo_data`: Traces (retention: 1h para demo)
- `redis_data`: Cache e rate limiting

### **Backup**
```bash
# Backup dos volumes
docker run --rm -v prometheus_data:/data -v $(pwd):/backup alpine tar czf /backup/prometheus-backup.tar.gz /data

# Backup das configurações
tar czf config-backup.tar.gz docker/
```

---

## 🔄 **Production Considerations**

### **Para usar em produção:**

1. **Secrets Management**
   ```yaml
   # Usar secrets externos
   environment:
     - SOLVIEW_API_KEY_FILE=/run/secrets/api_key
   secrets:
     - api_key
   ```

2. **Resource Limits**
   ```yaml
   deploy:
     resources:
       limits:
         memory: 1G
         cpus: '0.5'
   ```

3. **Health Checks**
   ```yaml
   healthcheck:
     test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
     interval: 30s
     timeout: 10s
     retries: 3
   ```

4. **Persistence**
   ```yaml
   # Usar volumes externos ou NFS
   volumes:
     - type: bind
       source: /data/prometheus
       target: /prometheus
   ```

---

## 📚 **Useful Commands**

```bash
# Parar tudo
docker-compose down

# Parar e remover volumes (CUIDADO!)
docker-compose down -v

# Rebuild apenas a demo app
docker-compose build solview-demo

# Escalar horizontalmente
docker-compose up -d --scale solview-demo=3

# Ver uso de recursos
docker stats

# Cleanup
docker system prune -f
docker volume prune -f
```

---

**Para suporte:** Consulte os logs de cada serviço e a documentação do Solview em `docs/`
