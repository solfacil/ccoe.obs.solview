# 📦 Integração do Solview

O `solview` foi projetado para oferecer **observabilidade unificada** — logging estruturado, métricas e tracing — em diversos tipos de aplicações Python. Este guia reúne as melhores práticas e exemplos para integrar o `solview` com frameworks e ambientes comuns.

---

### 🧩 Componentes Principais

| Componente | Finalidade | Principais recursos |
|-----------|------------|---------------------|
| `solview.logging` | Logging estruturado | JSON ECS, masking automático |
| `solview.metrics` | Coleta de métricas | Prometheus, middleware ASGI |
| `solview.tracing` | Tracing distribuído | OpenTelemetry, integração com FastAPI, SQL, HTTP |

---

## 🚀 Exemplos por Contexto

### ✅ FastAPI

```python
from fastapi import FastAPI
from solview.settings import SolviewSettings
from solview.logging import setup_logger
from solview.metrics import SolviewPrometheusMiddleware, prometheus_metrics_response
from solview.tracing import setup_tracer_from_env

app = FastAPI()

# Logging estruturado
setup_logger(SolviewSettings(service_name="api-clientes"))

# Métricas via Prometheus
app.add_middleware(SolviewPrometheusMiddleware, service_name="api-clientes")
app.add_route("/metrics", prometheus_metrics_response)

# Tracing via OTEL
setup_tracer_from_env(app)
```

---

### 🛠️ Celery

```python
from celery import Celery
from solview import Solview
from solview.metrics.core import METRIC_EXCEPTIONS

app = Celery("tasks", broker="redis://localhost:6379/0")
solview = Solview()

@app.task
def process_task(data):
    try:
        return solview.process(data)
    except Exception as e:
        METRIC_EXCEPTIONS.labels(
            method="task", path="process_task", exception_type=type(e).__name__, service_name="worker-tasks"
        ).inc()
        raise
```

> Combine com exportação de métricas via `start_http_server(9100)` se desejar scraping Prometheus em workers.

---

### 🐍 Scripts Python

```python
from solview.settings import SolviewSettings
from solview.logging import setup_logger
from solview import Solview

setup_logger(SolviewSettings(service_name="cli-importador"))

def main():
    solview = Solview()
    result = solview.process({"dados": "exemplo"})
    print(result)

if __name__ == "__main__":
    main()
```

---

## ⚙️ Configuração por Variáveis de Ambiente

Configure tudo via `.env` ou variáveis de ambiente:

```env
SOLVIEW_LOG_LEVEL=INFO
SOLVIEW_ENVIRONMENT=production
SOLVIEW_SERVICE_NAME=api-vendas
SOLVIEW_DOMAIN=vendas
SOLVIEW_SUBDOMAIN=checkout
SOLVIEW_VERSION=1.2.0

OTEL_SERVICE_NAME=api-vendas
OTEL_EXPORTER_OTLP_PROTOCOL=grpc
OTEL_EXPORTER_OTLP_ENDPOINT_HOST=otel-collector
OTEL_EXPORTER_OTLP_ENDPOINT_PORT=4317
```

---

## 🧪 Boas Práticas

- **Sempre defina `service_name` e `service_name`** nas integrações.
- **Use `mask_sensitive_data`** para proteger dados pessoais.
- **Configure corretamente o `/metrics`** para coleta por Prometheus.
- **Prefira gRPC no OpenTelemetry** para melhor performance.
- **Utilize logs estruturados com metadados via `extra={}`**.

---

## 🔗 Recursos Úteis

- [Documentação OpenTelemetry](https://opentelemetry.io/docs/)
- [Prometheus Python Client](https://github.com/prometheus/client_python)
- [Loguru](https://github.com/Delgan/loguru)
