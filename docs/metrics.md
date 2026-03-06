# 📊 Métricas Universais com Solview

O módulo **solview\.metrics** oferece uma maneira simples e padronizada de coletar métricas utilizando Prometheus, aplicável a aplicações web, workers, scripts batch, e muito mais.

---

## 🚀 Integração Rápida

Exemplo básico para FastAPI ou qualquer aplicação ASGI:

```python
from fastapi import FastAPI
from solview.metrics import SolviewPrometheusMiddleware, prometheus_metrics_response

app = FastAPI()
app.add_middleware(SolviewPrometheusMiddleware, service_name="api-financeiro")
app.add_route("/metrics", prometheus_metrics_response)
```

Agora, suas métricas estarão disponíveis no endpoint `/metrics`.

---

## 📈 Métricas Disponíveis

Métricas padrão já coletadas automaticamente:

| Métrica                            | Descrição                                                 |
| ---------------------------------- | --------------------------------------------------------- |
| `http_requests_total`              | Total de requisições HTTP por método e caminho            |
| `fastapi_responses_total`          | Total de respostas HTTP por método, caminho e status code |
| `fastapi_request_duration_seconds` | Latência das requisições por método e caminho             |
| `http_exceptions_total`            | Contagem de exceções por método, caminho e tipo           |
| `fastapi_requests_in_progress`     | Número atual de requisições em andamento                  |
| `fastapi_app_info`                 | Informações gerais do aplicativo em execução              |

---

## ⚙️ Métricas Personalizadas

Você pode criar métricas personalizadas facilmente:

```python
from prometheus_client import Counter

CUSTOM_TASK_SUCCESS = Counter(
    "fastapi_custom_task_success_total",
    "Quantidade de tarefas customizadas com sucesso.",
    ["task_name", "service_name"]
)

CUSTOM_TASK_SUCCESS.labels(task_name="enviar_email", service_name="worker-emails").inc()
```

---

## 🧑‍💻 Uso em Workers e Scripts

Integração simples em tasks ou scripts:

```python
from solview.metrics.core import METRIC_EXCEPTIONS

def processar_tarefa():
    try:
        # lógica da tarefa
        ...
    except Exception as exc:
        METRIC_EXCEPTIONS.labels(
            method="task", path="processar_tarefa", exception_type=type(exc).__name__, service_name="worker-tarefas"
        ).inc()
        raise
```

---

## 📡 Expondo Métricas para Prometheus

Expor métricas em workers com servidor HTTP básico do Prometheus:

```python
from prometheus_client import start_http_server

start_http_server(9100)  # expõe métricas em http://localhost:8000
```

---

## 🤖 Métricas MCP (FastMCP)

O módulo `solview.mcp` reutiliza a família de métricas `business_operations_*` para instrumentar servidores FastMCP:

| Métrica | Labels | Exemplo |
|---------|--------|---------|
| `business_operations_total` | `operation`, `app_name`, `status` | `operation="tool.buscar_cliente"` |
| `business_operations_duration_seconds` | `operation`, `app_name`, `status` | Latência da tool call |
| `business_operations_memory_bytes` | `operation`, `app_name`, `status` | Quando memory profiling ativo |

O label `operation` segue o padrão `<tipo>.<nome>`:
- Tool calls: `tool.nome_da_tool`
- Resource reads: `resource.uri`
- Prompt gets: `prompt.nome_do_prompt`

O MCP não expõe `/metrics` nativamente. Use `prometheus_client.start_http_server(port=9090)` para expor as métricas.

Para mais detalhes, veja o [Guia MCP](mcp.md).

---

## 🔴 Métricas Redis

O Solview oferece métricas Prometheus para operações Redis quando você usa o decorator `redis_client_instrumentation`:

| Métrica | Tipo | Labels | Descrição |
|---------|------|--------|-----------|
| `redis_operations_total` | Counter | `command`, `app_name`, `status` | Total de operações Redis |
| `redis_operations_duration_seconds` | Histogram | `command`, `app_name`, `status` | Duração das operações Redis |
| `redis_operations_errors_total` | Counter | `command`, `app_name`, `error_type` | Total de erros por tipo |
| `redis_operations_memory_bytes` | Histogram | `command`, `app_name`, `status` | Uso de memória (quando memory profiling ativo) |
| `redis_operations_memory_samples_total` | Counter | `command`, `app_name` | Amostras de memória coletadas |

Labels: `command` (ex: `get`, `set`), `app_name`, `status` (ex: `ok`, `error`), e `error_type` para erros.

---

## 🎯 Melhores Práticas

* Utilize labels consistentes como `service_name` para facilitar queries e dashboards.
* Mantenha métricas focadas em performance e estabilidade para melhor visibilidade.
* Evite métricas excessivamente granulares que possam causar overhead.

---

Agora, seu projeto está pronto para uma observabilidade completa com métricas robustas e fáceis de usar com Prometheus.
