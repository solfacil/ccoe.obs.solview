# 🚀 Guia de Deployment e Configuração

## 🎯 Visão Geral

Este guia cobre o deployment completo do **Solview** em diferentes ambientes: desenvolvimento, staging e produção, incluindo configurações de Kubernetes, Docker e cloud providers.

---

## 🏠 Ambiente de Desenvolvimento

### **1. Setup Local com Docker Compose**

```bash
# 1. Clonar repositório
git clone https://github.com/solfacil/solview
cd solview

# 2. Configurar ambiente
cp .env.example .env
# Editar .env conforme necessário

# 3. Iniciar stack completa
docker-compose up -d

# 4. Verificar serviços
docker-compose ps

# 5. Acessar interfaces
open http://localhost:3000  # Grafana (admin/admin)
open http://localhost:9090  # Prometheus
open http://localhost:3100  # Loki
```

### **2. Configuração de Desenvolvimento**

```bash
# .env para desenvolvimento
SOLVIEW_SERVICE_NAME=minha-api-dev
SOLVIEW_ENVIRONMENT=development
SOLVIEW_LOG_LEVEL=DEBUG
SOLVIEW_OTLP_ENDPOINT=http://localhost:4317
SOLVIEW_ENABLE_DATA_MASKING=false
SOLVIEW_TRACE_SAMPLING_RATE=1.0
SOLVIEW_METRICS_ENABLED=true
```

### **3. Aplicação de Exemplo**

```python
# app/main.py
from fastapi import FastAPI
from solview import SolviewSettings, setup_logger, setup_tracer
from solview.metrics import SolviewPrometheusMiddleware, prometheus_metrics_response

# Configuração para desenvolvimento
settings = SolviewSettings()

app = FastAPI(title="API de Desenvolvimento")

# Setup Solview
setup_logger(settings)
setup_tracer(settings, app)
app.add_middleware(SolviewPrometheusMiddleware, settings=settings)
app.add_route("/metrics", prometheus_metrics_response)

@app.get("/")
async def root():
    return {"message": "API funcionando com Solview!"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
```

### **4. Dockerfile para Desenvolvimento**

```dockerfile
# Dockerfile.dev
FROM python:3.11-slim

WORKDIR /app

# Instalar dependências
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copiar código
COPY . .

# Expor portas
EXPOSE 8000

# Comando para desenvolvimento
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
```

---

## 🧪 Ambiente de Staging

### **1. Configuração de Staging**

```bash
# .env.staging
SOLVIEW_SERVICE_NAME=minha-api-staging
SOLVIEW_ENVIRONMENT=staging
SOLVIEW_LOG_LEVEL=INFO
SOLVIEW_OTLP_ENDPOINT=http://otel-collector.staging.local:4317
SOLVIEW_ENABLE_DATA_MASKING=true
SOLVIEW_TRACE_SAMPLING_rate=0.5
SOLVIEW_METRICS_ENABLED=true
SOLVIEW_LOG_RETENTION_DAYS=14
```

### **2. Docker Compose para Staging**

```yaml
# docker-compose.staging.yml
version: '3.8'

x-logging: &default-logging
  driver: "json-file"
  options:
    max-size: "100m"
    max-file: "3"

services:
  app:
    build:
      context: .
      dockerfile: Dockerfile.staging
    environment:
      - SOLVIEW_SERVICE_NAME=minha-api-staging
      - SOLVIEW_ENVIRONMENT=staging
      - SOLVIEW_OTLP_ENDPOINT=http://otel-collector:4317
    deploy:
      replicas: 2
      resources:
        limits:
          memory: 512M
          cpus: 0.5
    logging: *default-logging
    depends_on:
      - otel-collector
    networks:
      - observability

  otel-collector:
    image: otel/opentelemetry-collector-contrib:latest
    command: ["--config=/etc/otel-collector-config.yaml"]
    volumes:
      - ./config/staging/otel-collector.yml:/etc/otel-collector-config.yaml
    ports:
      - "4317:4317"
      - "4318:4318"
    logging: *default-logging
    networks:
      - observability

  prometheus:
    image: prom/prometheus:latest
    volumes:
      - ./config/staging/prometheus.yml:/etc/prometheus/prometheus.yml
      - ./config/staging/rules:/etc/prometheus/rules
      - prometheus-data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--storage.tsdb.retention.time=30d'
      - '--web.console.libraries=/etc/prometheus/console_libraries'
      - '--web.console.templates=/etc/prometheus/consoles'
      - '--web.enable-lifecycle'
    ports:
      - "9090:9090"
    logging: *default-logging
    networks:
      - observability

volumes:
  prometheus-data:
  loki-data:
  tempo-data:

networks:
  observability:
    driver: bridge
```

### **3. Configuração de CI/CD**

```yaml
# .github/workflows/staging.yml
name: Deploy to Staging

on:
  push:
    branches: [ develop ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Build and push Docker image
      run: |
        docker build -t minha-api:staging .
        docker tag minha-api:staging registry.staging.local/minha-api:${{ github.sha }}
        docker push registry.staging.local/minha-api:${{ github.sha }}
    
    - name: Deploy to staging
      run: |
        ssh staging-server << 'EOF'
          cd /opt/minha-api
          docker-compose -f docker-compose.staging.yml pull
          docker-compose -f docker-compose.staging.yml up -d
        EOF
    
    - name: Run health checks
      run: |
        sleep 30
        curl -f http://staging.minha-api.com/health
        curl -f http://staging.minha-api.com/metrics
```

---

## 🏭 Ambiente de Produção

### **1. Configuração de Produção**

```bash
# .env.production
SOLVIEW_SERVICE_NAME=minha-api
SOLVIEW_ENVIRONMENT=production
SOLVIEW_LOG_LEVEL=INFO
SOLVIEW_OTLP_ENDPOINT=https://otel-collector.prod.local:4317
SOLVIEW_ENABLE_DATA_MASKING=true
SOLVIEW_TRACE_SAMPLING_RATE=0.05
SOLVIEW_METRICS_ENABLED=true

# Segurança
SOLVIEW_ENABLE_SECURITY_MIDDLEWARE=true
SOLVIEW_API_KEY_HEADER=X-API-Key
SOLVIEW_CORS_ORIGINS=https://minha-api.com,https://admin.minha-api.com

# Performance
SOLVIEW_MAX_SPAN_ATTRIBUTES=64
SOLVIEW_SPAN_EXPORT_BATCH_SIZE=1024
SOLVIEW_METRICS_EXPORT_INTERVAL_MS=30000
```

### **2. Dockerfile Otimizado para Produção**

```dockerfile
# Dockerfile.prod
# Build stage
FROM python:3.11-slim as builder

WORKDIR /app

# Instalar dependências de build
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Instalar dependências Python
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Production stage
FROM python:3.11-slim

# Criar usuário não-root
RUN groupadd -r appuser && useradd -r -g appuser appuser

WORKDIR /app

# Copiar dependências do build stage
COPY --from=builder /root/.local /home/appuser/.local

# Copiar código da aplicação
COPY --chown=appuser:appuser . .

# Configurar PATH
ENV PATH=/home/appuser/.local/bin:$PATH

# Mudar para usuário não-root
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# Expor porta
EXPOSE 8000

# Comando otimizado para produção
CMD ["python", "-m", "uvicorn", "app.main:app", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--workers", "4", \
     "--access-log", \
     "--no-server-header"]
```

### **3. Configuração de Load Balancer**

```nginx
# nginx.conf
upstream api_backend {
    least_conn;
    server app1.prod.local:8000 max_fails=3 fail_timeout=30s;
    server app2.prod.local:8000 max_fails=3 fail_timeout=30s;
    server app3.prod.local:8000 max_fails=3 fail_timeout=30s;
}

server {
    listen 80;
    listen 443 ssl http2;
    server_name minha-api.com;

    # SSL configuration
    ssl_certificate /etc/ssl/certs/minha-api.crt;
    ssl_certificate_key /etc/ssl/private/minha-api.key;

    # Security headers
    add_header X-Frame-Options DENY always;
    add_header X-Content-Type-Options nosniff always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Gzip compression
    gzip on;
    gzip_types text/plain application/json application/javascript text/css;

    # Locations
    location /health {
        access_log off;
        proxy_pass http://api_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /metrics {
        # Restringir acesso às métricas
        allow 10.0.0.0/8;
        deny all;
        proxy_pass http://api_backend;
    }

    location / {
        proxy_pass http://api_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts
        proxy_connect_timeout 5s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}
```

---

## ☸️ Deployment com Kubernetes

### **1. Namespace e ConfigMap**

```yaml
# k8s/namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: observability
  labels:
    name: observability

---
apiVersion: v1
kind: ConfigMap
metadata:
  name: solview-config
  namespace: observability
data:
  SOLVIEW_SERVICE_NAME: "minha-api"
  SOLVIEW_ENVIRONMENT: "production"
  SOLVIEW_LOG_LEVEL: "INFO"
  SOLVIEW_OTLP_ENDPOINT: "http://otel-collector.observability.svc.cluster.local:4317"
  SOLVIEW_ENABLE_DATA_MASKING: "true"
  SOLVIEW_TRACE_SAMPLING_RATE: "0.05"
  SOLVIEW_METRICS_ENABLED: "true"
```

### **2. Deployment da Aplicação**

```yaml
# k8s/app-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: minha-api
  namespace: observability
  labels:
    app: minha-api
    version: v1.0.0
spec:
  replicas: 3
  selector:
    matchLabels:
      app: minha-api
  template:
    metadata:
      labels:
        app: minha-api
        version: v1.0.0
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/port: "8000"
        prometheus.io/path: "/metrics"
    spec:
      containers:
      - name: api
        image: registry.prod.local/minha-api:latest
        ports:
        - containerPort: 8000
          name: http
        envFrom:
        - configMapRef:
            name: solview-config
        - secretRef:
            name: solview-secrets
        resources:
          requests:
            memory: "256Mi"
            cpu: "200m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: http
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: http
          initialDelaySeconds: 5
          periodSeconds: 5
        securityContext:
          allowPrivilegeEscalation: false
          runAsNonRoot: true
          runAsUser: 1000
          readOnlyRootFilesystem: true
          capabilities:
            drop:
            - ALL

---
apiVersion: v1
kind: Service
metadata:
  name: minha-api-service
  namespace: observability
  labels:
    app: minha-api
spec:
  selector:
    app: minha-api
  ports:
  - name: http
    port: 80
    targetPort: 8000
  type: ClusterIP
```

### **3. HorizontalPodAutoscaler**

```yaml
# k8s/hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: minha-api-hpa
  namespace: observability
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: minha-api
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
  behavior:
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
      - type: Percent
        value: 50
        periodSeconds: 60
    scaleUp:
      stabilizationWindowSeconds: 0
      policies:
      - type: Percent
        value: 100
        periodSeconds: 15
```

### **4. NetworkPolicy**

```yaml
# k8s/network-policy.yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: minha-api-netpol
  namespace: observability
spec:
  podSelector:
    matchLabels:
      app: minha-api
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: ingress-nginx
    - namespaceSelector:
        matchLabels:
          name: observability
    ports:
    - protocol: TCP
      port: 8000
  egress:
  - to:
    - namespaceSelector:
        matchLabels:
          name: observability
    ports:
    - protocol: TCP
      port: 4317  # OTLP
    - protocol: TCP
      port: 4318  # OTLP HTTP
  - to: []  # DNS
    ports:
    - protocol: UDP
      port: 53
```

---

## ☁️ Deployment em Cloud Providers

### **AWS EKS**

```yaml
# k8s/aws/service-monitor.yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: minha-api-metrics
  namespace: observability
  labels:
    app: minha-api
spec:
  selector:
    matchLabels:
      app: minha-api
  endpoints:
  - port: http
    path: /metrics
    interval: 30s
    scrapeTimeout: 10s

---
# k8s/aws/pod-disruption-budget.yaml
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: minha-api-pdb
  namespace: observability
spec:
  minAvailable: 2
  selector:
    matchLabels:
      app: minha-api
```

### **GCP GKE**

```yaml
# k8s/gcp/workload-identity.yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: minha-api-sa
  namespace: observability
  annotations:
    iam.gke.io/gcp-service-account: minha-api@project-id.iam.gserviceaccount.com

---
# Usar no deployment
spec:
  template:
    spec:
      serviceAccountName: minha-api-sa
```

### **Azure AKS**

```yaml
# k8s/azure/azure-identity.yaml
apiVersion: aadpodidentity.k8s.io/v1
kind: AzureIdentity
metadata:
  name: minha-api-identity
  namespace: observability
spec:
  type: 0
  resourceID: /subscriptions/subscription-id/resourcegroups/rg-name/providers/Microsoft.ManagedIdentity/userAssignedIdentities/minha-api-identity
  clientID: client-id

---
apiVersion: aadpodidentity.k8s.io/v1
kind: AzureIdentityBinding
metadata:
  name: minha-api-identity-binding
  namespace: observability
spec:
  azureIdentity: minha-api-identity
  selector: minha-api
```

---

## 🔧 Configuração de Monitoramento

### **1. Prometheus Configuration**

```yaml
# k8s/prometheus/prometheus-config.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: prometheus-config
  namespace: observability
data:
  prometheus.yml: |
    global:
      scrape_interval: 15s
      evaluation_interval: 15s
    
    rule_files:
      - "/etc/prometheus/rules/*.yml"
    
    scrape_configs:
      - job_name: 'kubernetes-pods'
        kubernetes_sd_configs:
        - role: pod
        relabel_configs:
        - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_scrape]
          action: keep
          regex: true
        - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_path]
          action: replace
          target_label: __metrics_path__
          regex: (.+)
        - source_labels: [__address__, __meta_kubernetes_pod_annotation_prometheus_io_port]
          action: replace
          regex: ([^:]+)(?::\d+)?;(\d+)
          replacement: $1:$2
          target_label: __address__
        - action: labelmap
          regex: __meta_kubernetes_pod_label_(.+)
        - source_labels: [__meta_kubernetes_namespace]
          action: replace
          target_label: kubernetes_namespace
        - source_labels: [__meta_kubernetes_pod_name]
          action: replace
          target_label: kubernetes_pod_name
```

### **2. Alerting Rules**

```yaml
# k8s/prometheus/alert-rules.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: prometheus-rules
  namespace: observability
data:
  solview-alerts.yml: |
    groups:
      - name: solview.rules
        rules:
          - alert: APIHighErrorRate
            expr: rate(http_responses_total{status_code=~"5.."}[5m]) / rate(http_responses_total[5m]) > 0.05
            for: 2m
            labels:
              severity: critical
              team: sre
            annotations:
              summary: "High error rate detected in {{ $labels.service_name }}"
              description: "Error rate is {{ $value | humanizePercentage }} for service {{ $labels.service_name }}"
              runbook_url: "https://runbooks.company.com/high-error-rate"
          
          - alert: APIHighLatency
            expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 1.0
            for: 5m
            labels:
              severity: warning
              team: sre
            annotations:
              summary: "High latency detected in {{ $labels.service_name }}"
              description: "95th percentile latency is {{ $value }}s for service {{ $labels.service_name }}"
          
          - alert: PodCrashLooping
            expr: rate(kube_pod_container_status_restarts_total[15m]) > 0
            for: 5m
            labels:
              severity: critical
              team: sre
            annotations:
              summary: "Pod {{ $labels.pod }} is crash looping"
              description: "Pod {{ $labels.pod }} in namespace {{ $labels.namespace }} is restarting frequently"
```

### **3. Grafana Dashboards**

```json
{
  "dashboard": {
    "title": "Solview API Monitoring",
    "tags": ["solview", "api", "observability"],
    "panels": [
      {
        "title": "Request Rate",
        "type": "stat",
        "targets": [
          {
            "expr": "sum(rate(http_requests_total{job=\"minha-api\"}[5m]))",
            "legendFormat": "Requests/sec"
          }
        ]
      },
      {
        "title": "Error Rate",
        "type": "stat",
        "targets": [
          {
            "expr": "sum(rate(http_responses_total{job=\"minha-api\",status_code=~\"5..\"}[5m])) / sum(rate(http_responses_total{job=\"minha-api\"}[5m])) * 100",
            "legendFormat": "Error %"
          }
        ],
        "thresholds": [
          {
            "color": "green",
            "value": 0
          },
          {
            "color": "yellow", 
            "value": 1
          },
          {
            "color": "red",
            "value": 5
          }
        ]
      }
    ]
  }
}
```

---

## 🔒 Masking (opcional em produção)

Para proteção de PII, configure o masking conforme o guia dedicado:

- [docs/masking.md](masking.md)

---

## 📊 Validação e Testes

### **1. Health Checks**

```bash
#!/bin/bash
# scripts/health-check.sh

APP_URL=${1:-http://localhost:8000}

echo "🔍 Validando deployment..."

# Health endpoint
echo "  ✅ Health check..."
curl -f "${APP_URL}/health" || exit 1

# Metrics endpoint
echo "  📊 Metrics check..."
curl -f "${APP_URL}/metrics" | grep -q "http_requests_total" || exit 1

# Trace context
echo "  🔍 Trace headers check..."
RESPONSE=$(curl -I "${APP_URL}/health" 2>/dev/null)
echo "$RESPONSE" | grep -q "traceparent" && echo "    ✅ Trace headers present" || echo "    ⚠️  No trace headers"

echo "🎉 Deployment validado com sucesso!"
```

### **2. Load Testing**

```python
# scripts/load-test.py
import asyncio
import aiohttp
import time
from typing import List

async def make_request(session: aiohttp.ClientSession, url: str) -> dict:
    start_time = time.time()
    try:
        async with session.get(url) as response:
            await response.text()
            return {
                'status': response.status,
                'duration': time.time() - start_time,
                'success': True
            }
    except Exception as e:
        return {
            'status': 0,
            'duration': time.time() - start_time,
            'success': False,
            'error': str(e)
        }

async def load_test(base_url: str, concurrent_requests: int, duration_seconds: int):
    """Execute load test"""
    print(f"🚀 Iniciando load test: {concurrent_requests} requests/sec por {duration_seconds}s")
    
    connector = aiohttp.TCPConnector(limit=100)
    async with aiohttp.ClientSession(connector=connector) as session:
        results = []
        start_time = time.time()
        
        while time.time() - start_time < duration_seconds:
            tasks = [
                make_request(session, f"{base_url}/health")
                for _ in range(concurrent_requests)
            ]
            
            batch_results = await asyncio.gather(*tasks)
            results.extend(batch_results)
            
            await asyncio.sleep(1)  # 1 request per second
        
        # Análise dos resultados
        total_requests = len(results)
        successful_requests = sum(1 for r in results if r['success'])
        average_duration = sum(r['duration'] for r in results) / total_requests
        
        print(f"📊 Resultados do Load Test:")
        print(f"  Total de requests: {total_requests}")
        print(f"  Requests bem-sucedidas: {successful_requests}")
        print(f"  Taxa de sucesso: {successful_requests/total_requests*100:.1f}%")
        print(f"  Duração média: {average_duration*1000:.1f}ms")

if __name__ == "__main__":
    import sys
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
    asyncio.run(load_test(base_url, 10, 60))
```

---

## 🔄 Estratégias de Deployment

### **1. Blue-Green Deployment**

```bash
#!/bin/bash
# scripts/blue-green-deploy.sh

NAMESPACE="observability"
APP_NAME="minha-api"
NEW_VERSION=$1

if [ -z "$NEW_VERSION" ]; then
    echo "Usage: $0 <version>"
    exit 1
fi

echo "🔵 Iniciando Blue-Green deployment para versão $NEW_VERSION"

# 1. Deploy da nova versão (Green)
echo "  📦 Fazendo deploy da versão Green..."
kubectl set image deployment/${APP_NAME} api=registry.prod.local/${APP_NAME}:${NEW_VERSION} -n ${NAMESPACE}

# 2. Aguardar rollout
echo "  ⏳ Aguardando rollout..."
kubectl rollout status deployment/${APP_NAME} -n ${NAMESPACE} --timeout=300s

# 3. Health check na nova versão
echo "  🔍 Fazendo health check..."
kubectl run health-check --rm -i --restart=Never --image=curlimages/curl -- \
  curl -f http://${APP_NAME}-service.${NAMESPACE}.svc.cluster.local/health

if [ $? -eq 0 ]; then
    echo "  ✅ Health check passou!"
    echo "  🟢 Deployment Green ativo e funcionando"
else
    echo "  ❌ Health check falhou!"
    echo "  🔴 Fazendo rollback..."
    kubectl rollout undo deployment/${APP_NAME} -n ${NAMESPACE}
    exit 1
fi

echo "🎉 Blue-Green deployment concluído com sucesso!"
```

### **2. Canary Deployment**

```yaml
# k8s/canary/canary-deployment.yaml
apiVersion: argoproj.io/v1alpha1
kind: Rollout
metadata:
  name: minha-api-canary
  namespace: observability
spec:
  replicas: 5
  strategy:
    canary:
      steps:
      - setWeight: 20
      - pause: {duration: 2m}
      - setWeight: 40
      - pause: {duration: 2m}
      - setWeight: 60
      - pause: {duration: 2m}
      - setWeight: 80
      - pause: {duration: 2m}
      canaryService: minha-api-canary
      stableService: minha-api-stable
      analysis:
        templates:
        - templateName: success-rate
        args:
        - name: service-name
          value: minha-api
  selector:
    matchLabels:
      app: minha-api
  template:
    metadata:
      labels:
        app: minha-api
    spec:
      containers:
      - name: api
        image: registry.prod.local/minha-api:latest
        ports:
        - containerPort: 8000
```

---

## 📈 Monitoramento de Deployment

### **1. Métricas de Deployment**

```promql
# Queries para monitorar deployment

# Taxa de sucesso do deployment
100 * (
  sum(rate(http_responses_total{status_code!~"5.."}[5m])) by (service_name) /
  sum(rate(http_responses_total[5m])) by (service_name)
)

# Latência durante deployment
histogram_quantile(0.95, 
  sum(rate(http_request_duration_seconds_bucket[5m])) by (service_name, le)
)

# Pods disponíveis
kube_deployment_status_replicas_available{deployment="minha-api"} /
kube_deployment_spec_replicas{deployment="minha-api"}
```

### **2. Alertas de Deployment**

```yaml
# k8s/prometheus/deployment-alerts.yaml
groups:
  - name: deployment.rules
    rules:
      - alert: DeploymentReplicasMismatch
        expr: kube_deployment_status_replicas_available != kube_deployment_spec_replicas
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Deployment {{ $labels.deployment }} has mismatched replicas"
          
      - alert: HighErrorRateDuringDeployment
        expr: |
          (
            sum(rate(http_responses_total{status_code=~"5.."}[2m])) by (service_name) /
            sum(rate(http_responses_total[2m])) by (service_name)
          ) > 0.10
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "High error rate during deployment for {{ $labels.service_name }}"
```

---

<div align="center">

**🚀 Deploy com confiança usando Solview em qualquer ambiente**

[🏠 Home](../README.md) | [📚 Docs](README.md) | [📋 Instrumentação](instrumentation-guide.md) | [🏗️ Arquitetura](architecture.md)

</div>
