# 📋 Changelog

Todas as mudanças notáveis do **Solview** serão documentadas neste arquivo.

O formato é baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.0.0/), e este projeto adere ao [Versionamento Semântico](https://semver.org/lang/pt-BR/).

---

## [2.2.0] - 2026-05-06
### ✨ Adicionado
- **`setup_tracer_provider()`** — cria/retorna `TracerProvider` + `MeterProvider` + Resource + Sampler e adiciona o `BatchSpanProcessor` com o exportador OTLP. Idempotente: chamadas subsequentes retornam o provider existente sem registrar processadores duplicados.
- **`setup_tracer_libs()`** — aplica somente as auto-instrumentações de biblioteca (Logging, HTTPX, AsyncPG, SQLAlchemy, http.client, Requests, Redis, AioPika). Idempotente — flag de módulo evita re-execução e logs duplicados.
- **`setup_tracer_fastapi(app)`** — aplica `FastAPIInstrumentor` e `prometheus-fastapi-instrumentator` em uma instância FastAPI. Idempotente por instância de `app`.
- Novas funções reexportadas a partir de `solview` e `solview.tracing`.

### 🔧 Modificado
- `setup_tracer(app=None)` agora é um *wrapper* que delega para as três funções acima, na ordem `setup_tracer_provider()` → `setup_tracer_libs()` → `setup_tracer_fastapi(app)`. Assinatura e comportamento observável preservados.

### 💡 Motivação
Resolve o *ordering bug* observado em consumidores como `agents-core`, em que a engine SQLAlchemy é criada em import-time (antes de `setup_tracer(app)` rodar dentro de `create_app()`). Como a função era monolítica, não era seguro chamá-la cedo e novamente com `app` (duplicava `BatchSpanProcessor`/`TracerProvider`). Agora é possível chamar `setup_tracer_provider()` + `setup_tracer_libs()` **antes** dos imports que tocam o banco, e `setup_tracer_fastapi(app)` depois de criar o `FastAPI`, sem duplicação.

#### Exemplo de uso recomendado
```python
from solview import (
    setup_settings,
    setup_tracer_provider,
    setup_tracer_libs,
    setup_tracer_fastapi,
)

setup_settings(...)
setup_tracer_provider()
setup_tracer_libs()  # ANTES de importar módulos que criam engine SQLAlchemy

from app.controllers import router  # imports que tocam DB

from fastapi import FastAPI
app = FastAPI()
app.include_router(router)
setup_tracer_fastapi(app)
```

---

## [2.1.5] - 2026-03-25
### ✨ Adicionado
- **Instrumentação RabbitMQ (aio-pika)** — decoradores `rabbitmq_publisher_instrumentation` e `rabbitmq_consumer_instrumentation` para instrumentação manual de operações RabbitMQ com tracing OpenTelemetry e métricas Prometheus
- **Auto-instrumentação aio-pika** — `AioPikaInstrumentor().instrument()` adicionado em `setup_tracer()` para tracing automático de operações aio-pika
- **Métricas RabbitMQ Publisher**: `rabbitmq_messages_published_total`, `rabbitmq_publisher_duration_seconds`, `rabbitmq_publisher_errors_total`, `rabbitmq_publisher_memory_bytes`, `rabbitmq_publisher_memory_samples_total` (labels: `routing_key`, `exchange`, `app_name`, `status`, `error_type`)
- **Métricas RabbitMQ Consumer**: `rabbitmq_messages_consumed_total`, `rabbitmq_consumer_processing_duration_seconds`, `rabbitmq_consumer_errors_total`, `rabbitmq_consumer_memory_bytes`, `rabbitmq_consumer_memory_samples_total` (labels: `queue`, `handler`, `app_name`, `status`, `error_type`)
- **Dependências**: `aio-pika>=9.6.2`, `opentelemetry-instrumentation-aio-pika>=0.60b1`
- **Métricas de resiliência RabbitMQ Consumer**: `rabbitmq_consumer_last_success_timestamp` (Gauge), `rabbitmq_consumer_consecutive_errors` (Gauge), `rabbitmq_consumer_unacked_messages` (Gauge) — para alertas de consumer parado, loop de falha, e backpressure
- **Testes completos** em `tests/instrumentation/test_rabbitmq.py` (22 testes: publisher success/error/memory, consumer success/error/memory, múltiplas filas, resiliência)

---

## [2.1.3] - 2026-03-10
### 🐛 Corrigido
- **Trace name (MCP)** — o trace aparecia com nome da primeira operação (ex.: "mcp-distribution SETEX") por não haver span raiz por request HTTP. Adicionado **`SolviewMCPASGIMiddleware`**: use-o como camada mais externa do app ASGI para que cada request tenha um span raiz no formato `METHOD path` (ex.: "POST /mcp") e as operações MCP/Redis fiquem como filhos. Documentação em `docs/mcp.md` e `docs/tracing.md`.
### 📝 Documentação
- **FastAPI** — esclarecido que na instrumentação FastAPI esse problema não existe: o `FastAPIInstrumentor` já cria um span raiz por request HTTP.

---

## [2.1.2] - 2026-03-09
### 🔧 Melhorado
- **Buckets de histograms** — adicionados buckets `15s, 30s, 60s, 120s, 300s` em `http_outgoing_requests_duration_seconds`, `business_operations_duration_seconds` e `kafka_message_processing_duration_seconds`. Corrige P50/P95/P99 que ficavam achatados em 10s quando operações ultrapassavam o último bucket finito.

---

## [2.1.1] - 2026-03-09
### 🐛 Corrigido
- **`http_client_instrumentation`** — corrigido bug onde `status="success"` e `status_code="exception"` eram registrados em `http_outgoing_requests_total` mesmo quando a resposta HTTP era 4xx/5xx. O `status` agora considera o status code real da response (>= 400 → `"error"`), e o `status_code` é extraído corretamente tanto do retorno da função quanto de exceções como `httpx.HTTPStatusError`.
- **`http_client_instrumentation`** — `error_type` no counter `http_outgoing_requests_errors_total` agora usa o nome da classe da exceção (ex: `"TimeoutException"`, `"ConnectError"`) em vez do genérico `"exception"`, permitindo alertas diferenciados por tipo de falha de rede.


## [2.1.0] - 2026-03-04

### ✨ Adicionado
- **Módulo `solview.mcp`** para observabilidade de servidores FastMCP (v2+)
- **`SolviewMCPMiddleware`** — middleware FastMCP que instrumenta tool calls, resource reads e prompt gets com spans OpenTelemetry e métricas Prometheus (`business_operations_*`)
- **`setup_tracer()` unificado** — aceita `app=None`; quando sem app (FastMCP/scripts), aplica apenas auto-instrumentações de biblioteca; quando com FastAPI, aplica também FastAPIInstrumentor e prometheus-fastapi-instrumentator
- **Dependência opcional** `solview[mcp]` via `pip install solview[mcp]`
- **Testes completos** em `tests/mcp/` (middleware, memory profiling, tracing, setup)
- **Documentação** `docs/mcp.md` com guia completo de uso
- `opentelemetry-instrumentation-redis` — auto-instrumentação para `redis` (sync) e `redis.asyncio` (async)
- `RedisInstrumentor().instrument()` em `setup_tracer()` (FastAPI e MCP)
- Decorator `redis_client_instrumentation(command="get")` para instrumentação manual com métricas Prometheus
- Métricas Redis: `redis_operations_total`, `redis_operations_duration_seconds`, `redis_operations_errors_total`, `redis_operations_memory_bytes`, `redis_operations_memory_samples_total` (labels: `command`, `app_name`, `status`, `error_type`)

---

## [2.0.1] - 2025-08-20

### ✨ Adicionado
- **Correlação automática** trace-to-metrics no Grafana com sintaxe corrigida
- **Service Graph** automático via Tempo metrics generator
- **Masking automático** de dados sensíveis (LGPD/GDPR compliance)
- **Instrumentação zero-code** para FastAPI com middlewares
- **Métricas padronizadas** compatíveis com OpenTelemetry
- **Logs estruturados** em JSON com correlação automática
- **Scripts de observabilidade** para testes e validação
- **Documentação completa** para uso empresarial

### 🔧 Modificado
- **Métricas renomeadas** para padrão universal (`http_requests_total`, `http_responses_total`)
- **Configuração simplificada** via variáveis de ambiente
- **Performance otimizada** com batching e sampling configurável
- **Segurança aprimorada** com middleware de validação

### 🐛 Corrigido
- **Interpolação de traces** no Grafana usando sintaxe `${__span.tags["service.name"]}`
- **Correlação automática** funcionando entre traces, logs e métricas
- **Service Graph** aparecendo corretamente no Grafana
- **Propagação de contexto** entre microsserviços
- **Masking de PII** em logs e traces

### 🔒 Segurança
- **Data masking** automático para campos sensíveis
- **Validação de entrada** em todos os endpoints
- **Headers de segurança** configuráveis
- **Auditoria de acesso** com logs estruturados

---

## [2.0.0] - 2025-08-15

### ✨ Adicionado
- **Reescrita completa** da biblioteca para Python 3.11+
- **Suporte nativo** ao OpenTelemetry
- **Integração total** com stack LGTM (Loki, Grafana, Tempo, Mimir)
- **Auto-instrumentação** para FastAPI, SQLAlchemy, HTTPX
- **Configuração unificada** via Pydantic Settings

### 💥 Breaking Changes
- **API completamente nova** - migração necessária da v1.x
- **Dependências atualizadas** - Python 3.11+ obrigatório
- **Configuração modificada** - variáveis de ambiente padronizadas

---

## [1.2.3] - 2023-12-10

### 🐛 Corrigido
- Bug crítico em logging assíncrono
- Vazamento de memória em traces de longa duração
- Compatibilidade com FastAPI 0.104+

---

## [1.2.0] - 2023-11-15

### ✨ Adicionado
- Suporte inicial ao OpenTelemetry
- Métricas customizadas via Prometheus
- Logs estruturados com Loguru

### 🔧 Modificado
- Performance melhorada em 40%
- Redução de overhead de instrumentação

---

## [1.1.0] - 2023-10-01

### ✨ Adicionado
- Instrumentação automática para FastAPI
- Dashboard básico do Grafana
- Alertas do Prometheus

---

## [1.0.0] - 2025-06-01

### ✨ Primeira versão
- **Logging básico** estruturado
- **Métricas** HTTP simples
- **Tracing** manual com Jaeger
- **Documentação** inicial

---

## 🤝 Contribuidores

### 👥 **Core Team**
- **Jefferson Martins** - Arquiteto Principal (@jmartins)
- **CCOE Team** - Centro de Excelência em Observabilidade
- **SRE Team** - Reliability Engineering

### 🎯 **Agradecimentos Especiais**
- **ChatGPT 5.0** - Solução da interpolação de traces no Grafana
- **OpenTelemetry Community** - Especificações e SDKs
- **Grafana Labs** - Stack LGTM e documentação
- **Solfacil Engineering** - Feedback e casos de uso

---

## 📞 Suporte e Contato

### 🏢 **Suporte Interno (Solfacil)**
- **Email**: ccoe@solfacil.com.br
- **Teams**: Canal #observabilidade
- **Confluence**: [Solview Wiki](https://solfacil.atlassian.net)
- **Jira**: Projeto CCOE para issues e features

### 🌐 **Comunidade**
- **GitHub Issues**: Para bugs e feature requests
- **GitHub Discussions**: Para dúvidas e ideias
- **Internal Wiki**: Documentação colaborativa
- **Brown Bags**: Sessões semanais de Q&A

### 📚 **Documentação**
- **Docs**: [Documentação completa](docs/README.md)

---

<div align="center">

**📋 Acompanhe a evolução do Solview**

[🏠 Home](README.md) | [📚 Docs](docs/README.md) | [🚀 Quick Start](README.md#-quick-start)

---

*Mantido com ❤️ pela equipe de **Centro de Excelência em Observabilidade** da Solfacil*

</div>
