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
| `fastapi_requests_total`           | Total de requisições HTTP por método e caminho            |
| `fastapi_responses_total`          | Total de respostas HTTP por método, caminho e status code |
| `fastapi_request_duration_seconds` | Latência das requisições por método e caminho             |
| `fastapi_exceptions_total`         | Contagem de exceções por método, caminho e tipo           |
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

## 🎯 Melhores Práticas

* Utilize labels consistentes como `service_name` para facilitar queries e dashboards.
* Mantenha métricas focadas em performance e estabilidade para melhor visibilidade.
* Evite métricas excessivamente granulares que possam causar overhead.

---

Agora, seu projeto está pronto para uma observabilidade completa com métricas robustas e fáceis de usar com Prometheus.
