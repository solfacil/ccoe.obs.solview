# 📦 Integração do Solview

O `solview` foi projetado para oferecer **observabilidade unificada** — logging estruturado, métricas e tracing — em diversos tipos de aplicações Python. Este guia reúne as melhores práticas e exemplos para integrar o `solview` com frameworks e ambientes comuns.

---

### 🧩 Componentes Principais

| Componente | Finalidade | Principais recursos |
|-----------|------------|---------------------|
| `solview.logging` | Logging estruturado | JSON ECS, masking automático |
| `solview.metrics` | Coleta de métricas | Prometheus, middleware ASGI |
| `solview.tracing` | Tracing distribuído | OpenTelemetry, integração com FastAPI, SQL, HTTP, Redis |
| `solview.mcp` | Observabilidade MCP | Middleware FastMCP, usa `setup_tracer()` sem app |
| `solview.instrumentation.redis` | Instrumentação Redis | `redis_client_instrumentation`, métricas `redis_operations_*` |

---

## 🚀 Exemplos por Contexto

### ✅ FastAPI

```python
from fastapi import FastAPI
from solview import SolviewSettings, setup_logger, setup_tracer
from solview.metrics import SolviewPrometheusMiddleware, prometheus_metrics_response

app = FastAPI()

# Logging estruturado
setup_logger(SolviewSettings(service_name="api-clientes"))

# Métricas via Prometheus
app.add_middleware(SolviewPrometheusMiddleware, service_name="api-clientes")
app.add_route("/metrics", prometheus_metrics_response)

# Tracing via OTEL
setup_tracer(SolviewSettings(service_name="api-clientes"), app)
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

### 🤖 FastMCP (Servidores MCP)

```python
from fastmcp import FastMCP
from prometheus_client import start_http_server
from solview import SolviewSettings, setup_settings, setup_logger, setup_tracer
from solview.mcp import SolviewMCPMiddleware

# Observabilidade
setup_settings(SolviewSettings(service_name="mcp-assistente"))
setup_logger()
setup_tracer()

# Métricas Prometheus (MCP não tem /metrics nativo)
start_http_server(port=9090)

# Servidor MCP instrumentado
mcp = FastMCP("Assistente")
mcp.add_middleware(SolviewMCPMiddleware())

@mcp.tool
async def consultar_saldo(conta: str) -> str:
    return f"Saldo da conta {conta}: R$ 1.234,56"
```

> Instale com `pip install solview[mcp]`. Chamadas a httpx, asyncpg e sqlalchemy dentro das tools são automaticamente rastreadas via OpenTelemetry.

---

### 🐍 Scripts Python

```python
from solview import SolviewSettings, setup_logger

setup_logger(SolviewSettings(service_name="cli-importador"))

def main():
    # lógica do script
    pass

if __name__ == "__main__":
    main()
```

---

## ⚙️ Configuração por Variáveis de Ambiente

Configure tudo via `.env` ou variáveis de ambiente:

```env
LOG_LEVEL=INFO
ENVIRONMENT=production
SERVICE_NAME=api-vendas
DOMAIN=vendas
SUBDOMAIN=checkout
VERSION=1.2.0

OTLP_EXPORTER_HOST=otel-collector
OTEL_SERVICE_NAMESPACE=api-vendas
```

> **Nota:** Configurações como `otlp_exporter_protocol` e `otlp_exporter_port` são definidas programaticamente via `TracingSettings`.

---

## 🧪 Boas Práticas

- **Sempre defina `service_name`** nas integrações.
- **Use `mask_sensitive_data`** para proteger dados pessoais.
- **Configure corretamente o `/metrics`** para coleta por Prometheus.
- **Prefira gRPC no OpenTelemetry** para melhor performance.
- **Utilize logs estruturados com metadados via `extra={}`**.

---

## 🔗 Recursos Úteis

- [Documentação OpenTelemetry](https://opentelemetry.io/docs/)
- [Prometheus Python Client](https://github.com/prometheus/client_python)
- [Loguru](https://github.com/Delgan/loguru)
