# 📦 Integração do Solview

O `solview` foi projetado para oferecer **observabilidade unificada** — logging estruturado, métricas e tracing — em diversos tipos de aplicações Python. Este guia reúne as melhores práticas e exemplos para integrar o `solview` com frameworks e ambientes comuns.

Versão Solview: `2.2.0+` (com funções separadas para tracing)

---

### 🧩 Componentes Principais

| Componente | Finalidade | Principais recursos |
|-----------|------------|---------------------|
| `solview.logging` | Logging estruturado | JSON ECS, masking automático |
| `solview.metrics` | Coleta de métricas | Prometheus, middleware ASGI |
| `solview.tracing` | Tracing distribuído | OpenTelemetry, integração com FastAPI, SQL, HTTP, Redis |
| `solview.mcp` | Observabilidade MCP | Middleware FastMCP, usa `setup_tracer()` sem app |
| `solview.instrumentation.redis` | Instrumentação Redis | `redis_client_instrumentation`, métricas `redis_operations_*` |
| `solview.instrumentation.script` | Scripts e Cronjobs | `script_job_instrumentation`, push via Prometheus Pushgateway |

---

## 🚀 Exemplos por Contexto

### ✅ FastAPI (Simples)

```python
from fastapi import FastAPI
from solview import setup_logger, setup_tracer
from solview.metrics import SolviewPrometheusMiddleware, prometheus_metrics_response

app = FastAPI()

# Setup logging
setup_logger()

# Setup tracing (provider + libs + fastapi)
setup_tracer(app)

# Métricas
app.add_middleware(SolviewPrometheusMiddleware)
app.add_route("/metrics", prometheus_metrics_response)
```

### ✅ FastAPI (Com Engine em Import-time)

```python
from solview import setup_settings, setup_tracer_provider, setup_tracer_libs, setup_tracer_fastapi
from solview.metrics import SolviewPrometheusMiddleware, prometheus_metrics_response

# 1. Settings
setup_settings(SolviewSettings(service_name="api-clientes"))

# 2. Tracer provider (antes de imports de DB)
setup_tracer_provider()

# 3. Lib instrumentation (antes de imports de DB)
setup_tracer_libs()

# 4. Agora é seguro importar módulos que tocam DB
from app.controllers import router
from app.db import engine

# 5. FastAPI
from fastapi import FastAPI
app = FastAPI()
app.include_router(router)

# 6. Tracer FastAPI
setup_tracer_fastapi(app)

# 7. Métricas
app.add_middleware(SolviewPrometheusMiddleware)
app.add_route("/metrics", prometheus_metrics_response)
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
from solview import setup_settings, setup_tracer
from solview.mcp import SolviewMCPMiddleware

# Observabilidade
setup_settings(SolviewSettings(service_name="mcp-assistente"))
setup_tracer()  # Provider + libs (sem FastAPI instrumentation)

# Métricas Prometheus (MCP não tem /metrics nativo)
start_http_server(port=9090)

# Servidor MCP instrumentado
mcp = FastMCP("Assistente")
mcp.add_middleware(SolviewMCPMiddleware())

@mcp.tool
async def consultar_saldo(conta: str) -> str:
    return f"Saldo da conta {conta}: R$ 1.234,56"
```

> Instale com `uv add solview[mcp]`. Chamadas a httpx, asyncpg e sqlalchemy dentro das tools são automaticamente rastreadas via OpenTelemetry.

---

### 🐍 Scripts e Cronjobs (Pushgateway)

Scripts de curta duração não podem servir um endpoint HTTP persistente. Use o modelo push com o Pushgateway:

```python
from solview import setup_settings, setup_logger, script_job_instrumentation
from solview.settings import SolviewSettings

setup_settings(SolviewSettings(service_name="cli-importador"))
setup_logger()


@script_job_instrumentation(
    "importacao-clientes",
    gateway_url="http://pushgateway:9091",
)
def importar_clientes():
    # lógica do script
    pass


if __name__ == "__main__":
    importar_clientes()
    # ↑ métricas são enviadas automaticamente ao Pushgateway ao finalizar
```

> Veja o guia completo em [📋 Scripts e Cronjobs](scripts-e-cronjobs.md) — alertas recomendados, configuração do Pushgateway, boas práticas e troubleshooting.

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
