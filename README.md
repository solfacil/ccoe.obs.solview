# ☀️ solview

**Observabilidade clara como o Sol**

`solview` é uma biblioteca Python única para logging estruturado, métricas e tracing, criada pela Solfácil para unificar e padronizar a observabilidade de todas as aplicações.  
Seu foco é facilitar integração com stacks modernas (Loki, ELK, Prometheus, OpenTelemetry, etc.), com zero dor de cabeça, seja no desenvolvimento local ou em produção no Kubernetes.

---

## Features

- **Logging estruturado** (JSON ECS): pronto para ELK, Grafana, Loki, StackDriver etc.
- **Métricas integradas**: exportação e customização via Prometheus (*em desenvolvimento*).
- **Tracing distribuído**: facilmente plugável com OpenTelemetry/Jaeger/Tempo (*em desenvolvimento*).
- **Configuração única via env vars ou `.env` local**
- **Máscara automática de dados sensíveis**
- **Integração pronta para FastAPI, Celery, scripts, workers e mais**

---

## Instalação

```bash
pip install solview
```

---

## Configuração

Por padrão, o `solview` lê configurações das environment variables.  
Localmente, pode usar um arquivo `.env` na raiz do projeto, por exemplo:

```
# .env exemplo
SOLVIEW_LOG_LEVEL=INFO
SOLVIEW_ENVIRONMENT=production
SOLVIEW_SERVICE_NAME=api-pedidos
SOLVIEW_DOMAIN=vendas
SOLVIEW_SUBDOMAIN=checkout
SOLVIEW_VERSION=2.0.0
```

**No Kubernetes:**  
Configure suas env vars via `deployment.yaml`, `ConfigMap` ou `Secret`.

---

## Logging estruturado

### Setup básico em qualquer app Python

```python
from solview.settings import SolviewSettings
from solview.logging import setup_logger

settings = SolviewSettings() # Carrega de env vars ou .env
setup_logger(settings)

from loguru import logger
logger.info("API inicializada com sucesso", extra={"request_id": "abc-123"})
```

- **Em ambiente de desenvolvimento:** logs coloridos/humanos no terminal.
- **Em produção:** logs JSON compatíveis com ELK, Loki, DataDog etc.

### Máscara de dados sensíveis

```python
from solview.common.masking import mask_sensitive_data

logger.info(mask_sensitive_data("CPF do cliente: 12345678909, email=joao@email.com"))
```

---

## Exemplos de integração

### FastAPI

```python
from solview.settings import SolviewSettings
from solview.logging import setup_logger

app = FastAPI()
setup_logger(SolviewSettings(service_name="api-clientes"))
```

---

## Métricas & Tracing

- Estrutura pronta para:
  - **Métricas**: Exportação Prometheus.
  - **Tracing**: Plug-and-play com OpenTelemetry.
- Em breve exemplos e helpers integrados para FastAPI.

---

## Convenções

- Todas as configurações via env var, compatível com Docker/Kubernetes.
- Logs no formato ECS quando em produção; humano/híbrido no desenvolvimento.
- Módulo masking aplicado onde necessário.
- Estrutura extensível: basta importar, inicializar, usar!

---
---
## Métricas universais (`solview.metrics`)

O módulo `solview.metrics` padroniza as métricas para qualquer tipo de app Python (web, worker, script, etc) usando Prometheus e integração opcional com OpenTelemetry para tracing.

### Principais vantagens

- **Métricas sem acoplamento ao framework:** Prefixos universais (`solview_`) e labels padronizadas (`service_name`, `method`, `path`, etc), prontas para múltiplos serviços.
- **Fácil de plugar:** Middleware para ASGI, endpoint pronto de `/metrics`, integração simples com FastAPI, Starlette, Quart, etc.
- **Extensibilidade:** Possível criar métricas customizadas para workers, handlers, jobs e scripts.
- **Compatível com Prometheus, Grafana, e exporters do ecossistema cloud/k8s.**

---

### Como usar com FastAPI

```python
from fastapi import FastAPI
from solview.metrics import SolviewPrometheusMiddleware, prometheus_metrics_response

app = FastAPI()
app.add_middleware(SolviewPrometheusMiddleware, service_name="api-financeiro")
app.add_route("/metrics", prometheus_metrics_response)
```

Agora, ao acessar `/metrics`, as métricas estarão no padrão OpenMetrics, prontas para scrape do Prometheus.

---

### Exemplos de métricas coletadas

- `fastapi_requests_total`: Total de requisições separadas por método, caminho e app.
- `fastapi_responses_total`: Contagem por status code.
- `fastapi_request_duration_seconds`: Latência por endpoint (histograma).
- `fastapi_exceptions_total`: Exceções agrupadas por rota, método e tipo.
- `fastapi_requests_in_progress`: Requisições em andamento simultaneamente.
- `fastapi_app_info`: Info do app rodando.

---

### Exemplo de integração com Celery ou outro worker

Para medir jobs/handlers em workers, use os helpers diretamente:

```python
from solview.metrics.core import METRIC_INFO, METRIC_EXCEPTIONS

def processa_fatura():
    METRIC_INFO.labels(service_name="worker-faturas").set(1)
    try:
        # Lógica do worker
        ...
    except Exception as exc:
        METRIC_EXCEPTIONS.labels(method="task", path="processa_fatura", exception_type=type(exc).__name__, service_name="worker-faturas").inc()
        raise
```
> Integre essas métricas a um endpoint Prometheus HTTP simples, se desejar expor para scraping em workers!

---

### Como criar métricas customizadas

Basta instanciar novas métricas no seu código e seguir a nomenclatura/labels universais.  
Sugestão para tasks assíncronas, filas, ou eventos customizados.

```python
from prometheus_client import Counter

CUSTOM_TASK_SUCCESS = Counter("fastapi_custom_task_success_total", "Quantidade de tarefas customizadas com sucesso.", ["task_name", "service_name"])

CUSTOM_TASK_SUCCESS.labels(task_name="enviar_email", service_name="worker-emails").inc()
```

---

### Boas práticas e dicas

- Sempre defina `service_name` ao inicializar o middleware ou novas métricas, facilitando queries e dashboards multi-serviço.
- Para múltiplos apps na mesma instância, cuide para não duplicar nomes/labels em métricas.
- Use as métricas padrões para monitoramento e alertas básicos de SLA, erros e disponibilidade.
- Métricas customizadas podem complementar business metrics, mas mantenha a compatibilidade Prometheus/OpenMetrics.

---

### Utilizando com outros frameworks

Qualquer app ASGI (Starlette, Quart, etc.) pode usar o `SolviewPrometheusMiddleware` e o `prometheus_metrics_response` para expor métricas.
Se precisar de integração para WSGI, consulte a [documentação do prometheus_client](https://github.com/prometheus/client_python).

---

## Roadmap

- [x] Logging estruturado pronto para produção
- [ ] Exposição e coleta de métricas Prometheus
- [ ] Tracing distribuído via OpenTelemetry
- [ ] Suporte para alertas
- [ ] Handlers avançados, exemplos para diferentes stacks

---

## Contribuindo

Contribuições são bem-vindas! Antes de abrir um PR, consulte o [CONTRIBUTING.md](CONTRIBUTING.md).

---

## Licença

MIT