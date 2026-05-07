# 🔍 Tracing Distribuído com Solview

O módulo solview.tracing fornece tracing distribuído simples e eficiente usando o OpenTelemetry, facilitando a integração com FastAPI e outras aplicações Python modernas.

Versão: `2.2.0+`

⸻

## 🚀 Integração Rápida

Exemplo básico para integrar tracing em uma aplicação FastAPI:

```python
from fastapi import FastAPI
from solview import setup_tracer

app = FastAPI()
setup_tracer(app)
```

Este setup inicializa automaticamente o tracing baseado em variáveis de ambiente padrão (recomendado para a maioria dos casos).

⸻

## 🛠️ Configuração por Variáveis de Ambiente

Configure seu tracing utilizando as seguintes variáveis:

OTEL_SERVICE_NAME=api-clientes
OTEL_SERVICE_VERSION=1.0.0
OTEL_EXPORTER_OTLP_PROTOCOL=grpc
OTEL_EXPORTER_OTLP_ENDPOINT=localhost
OTEL_EXPORTER_OTLP_ENDPOINT_PORT=4317
OTEL_EXPORTER_OTLP_HTTP_ENCRYPTED=false
OTEL_EXPORTER_OTLP_AUTH_TOKEN=<token>
OTEL_SQLALCHEMY_ENABLE_COMMENTER=false


⸻

## ⚙️ Configuração Personalizada

Caso queira uma configuração mais detalhada, utilize o método setup_tracer:

```python
from fastapi import FastAPI
from solview.tracing import setup_tracer

app = FastAPI()

setup_tracer(
    app=app,
    service_name="api-clientes",
    service_version="1.0.0",
    deployment_name="prod",
    otlp_exporter_protocol="http",  # ou "grpc"
    otlp_exporter_host="otel-collector",
    otlp_exporter_port=4318,
    otlp_exporter_http_encrypted=True,
    otlp_agent_auth_token="my-auth-token",
    otlp_sqlalchemy_enable_commenter=True
)
```

⸻

## 📡 Exportadores OTLP Suportados
	•	gRPC: Mais eficiente e padrão.
	•	HTTP: Alternativa útil em ambientes que não permitem conexões gRPC.

⸻

## 📦 Recursos Instrumentados Automaticamente
	•	FastAPI: Instrumentação completa das requisições HTTP.
	•	AsyncPG: Tracing de operações no PostgreSQL assíncrono.
	•	SQLAlchemy: Tracing de queries SQL com comentários opcionais.
	•	HTTPX: Requisições HTTP realizadas com HTTPX.
	•	Logging Python: Integra logs padrão com tracing.
	•	Redis: Operações Redis sync (`redis`) e async (`redis.asyncio`) via `opentelemetry-instrumentation-redis`.

⸻

## 📋 Exemplo de Context Propagation

Injete ou extraia o contexto de tracing em requisições HTTP:

```python
from solview.tracing.propagators import inject_correlation_context, extract_correlation_context

# Injeta contexto em headers HTTP
headers = {}
inject_correlation_context(headers)

# Extrai contexto recebido de uma requisição HTTP
span = extract_correlation_context(headers)
```

⸻

## 📌 Funções Públicas de Tracing (v2.2.0+)

A partir da versão `2.2.0`, o setup de tracing foi refatorado em três funções públicas **idempotentes** para maior controle e para resolver um bug de ordering com SQLAlchemy:

### 1. **`setup_tracer_provider() -> TracerProvider`**

Cria o `TracerProvider` (provedor de spans) com `MeterProvider` (métricas), Resource, Sampler e exportadores OTLP.

**Assinatura:**
```python
def setup_tracer_provider() -> TracerProvider:
    """
    Cria/retorna TracerProvider + MeterProvider + Resource + Sampler e
    adiciona o BatchSpanProcessor com exportador OTLP.
    
    Idempotente: chamadas subsequentes retornam o TracerProvider já criado
    sem registrar processadores duplicados.
    
    Em modo PYTHON_ENV=unittest com use_console_exporter_on_unittest,
    usa SimpleSpanProcessor(ConsoleSpanExporter()) para testes.
    """
```

**Exemplo:**
```python
from solview import setup_tracer_provider

provider = setup_tracer_provider()
```

### 2. **`setup_tracer_libs() -> None`**

Auto-instrumenta as principais bibliotecas: Logging, HTTPX, AsyncPG, SQLAlchemy, http.client, Requests, Redis, AioPika.

**Assinatura:**
```python
def setup_tracer_libs() -> None:
    """
    Auto-instrumentações de bibliotecas Python:
    - Logging (integra logs com tracing)
    - HTTPX (requisições HTTP assíncronas)
    - AsyncPG (driver PostgreSQL assíncrono)
    - SQLAlchemy (ORM SQL)
    - http.client (HTTP nativo Python)
    - Requests (requisições HTTP síncronas)
    - Redis (operações Redis)
    - AioPika (RabbitMQ)
    
    Aplica OTEL_SEMCONV_STABILITY_OPT_IN=http automaticamente.
    
    Idempotente: chamadas subsequentes não re-instrumentam.
    """
```

**Exemplo:**
```python
from solview import setup_tracer_libs

setup_tracer_libs()
```

### 3. **`setup_tracer_fastapi(app) -> None`**

Instrumenta uma instância FastAPI com `FastAPIInstrumentor` + `prometheus-fastapi-instrumentator`.

**Assinatura:**
```python
def setup_tracer_fastapi(app: FastAPI) -> None:
    """
    Instrumenta instância FastAPI com spans por request HTTP.
    
    Idempotente por instância de app: cada app é instrumentado uma única vez.
    
    Parâmetros:
        app (FastAPI): Instância da aplicação FastAPI
    """
```

**Exemplo:**
```python
from fastapi import FastAPI
from solview import setup_tracer_fastapi

app = FastAPI()
setup_tracer_fastapi(app)
```

### 4. **`setup_tracer(app=None)` — Wrapper Compatível (Recomendado)**

Função wrapper que chama as três acima em ordem. **Retrocompatível** com código antigo.

**Assinatura:**
```python
def setup_tracer(app: FastAPI = None) -> None:
    """
    Wrapper idempotente que chama setup_tracer_provider(),
    setup_tracer_libs() e setup_tracer_fastapi(app).
    
    Preserva compatibilidade com versões anteriores.
    Recomendado para a maioria dos casos.
    
    Parâmetros:
        app (FastAPI, opcional): Instância FastAPI. Se None, pula FastAPI
                                 instrumentation (útil para FastMCP).
    """
```

**Exemplo com FastAPI:**
```python
from fastapi import FastAPI
from solview import setup_tracer

app = FastAPI()
setup_tracer(app)  # Chama provider → libs → fastapi automaticamente
```

**Exemplo com FastMCP (sem app):**
```python
from solview import setup_tracer

setup_tracer()  # Chama provider → libs (sem FastAPI instrumentation)
```

---

## ⚠️ Ordering Bug com SQLAlchemy / Engines em Import-time

**Problema:** Em consumidores como `agents-core`, a engine SQLAlchemy é criada em import-time (nível de módulo), antes de `setup_tracer(app)` rodar dentro de `create_app()`.

O `SQLAlchemyInstrumentor().instrument()` faz patch em `create_async_engine` para engines **futuras** — engines pré-existentes não recebem os listeners `before_cursor_execute`/`after_cursor_execute`, e `db.statement` nunca aparece nos spans. Apenas `connect`/`begin` via AsyncPG são vistos no Tempo.

**Solução:** Chamar `setup_tracer_provider()` + `setup_tracer_libs()` **ANTES** dos imports que tocam DB, e `setup_tracer_fastapi(app)` após criar a app:

```python
# main.py ou app/__init__.py
from solview import (
    setup_settings,
    setup_tracer_provider,
    setup_tracer_libs,
    setup_tracer_fastapi,
)

# 1. Configurar settings PRIMEIRO
setup_settings(...)

# 2. Setup tracer provider (cria TracerProvider + MeterProvider)
setup_tracer_provider()

# 3. Setup lib instrumentation (patch em create_async_engine ANTES de imports)
setup_tracer_libs()

# 4. AGORA é seguro importar módulos que criam engine SQLAlchemy
from app.controllers import router  # Imports que tocam DB
from app.db import engine

# 5. Criar FastAPI app
from fastapi import FastAPI
app = FastAPI()
app.include_router(router)

# 6. Instrumentar FastAPI
setup_tracer_fastapi(app)
```

**Benefício:** O `SQLAlchemyInstrumentor` faz patch ANTES da engine ser criada, garantindo que listeners sejam registrados e `db.statement` apareça nos spans.

**Alternativa simples (sem engine em import-time):** Se a engine é criada lazy (ex.: em factory function), você pode usar o wrapper `setup_tracer(app)` da forma tradicional — não há ordering bug.

---

## 🤖 Tracing para MCP (FastMCP)

Para servidores FastMCP (v2+), use `setup_tracer()` ou as três funções separadas:

```python
from solview import setup_settings, setup_tracer
from solview.mcp import SolviewMCPMiddleware

# Configuração unificada
setup_settings(SolviewSettings(service_name="meu-mcp-server"))
setup_tracer()  # Provider + libs (sem FastAPI instrumentation)

# Ou as três em separado:
# setup_tracer_provider()
# setup_tracer_libs()
# (não precisa setup_tracer_fastapi para MCP)
```

Quando `app` não é passado (ou é `None`), o `setup_tracer()` configura o TracerProvider e ativa as auto-instrumentações de biblioteca (httpx, requests, asyncpg, sqlalchemy, redis, logging), sem aplicar instrumentação específica de FastAPI.

O `SolviewMCPMiddleware` gera spans para cada operação MCP:
- `mcp.tool.<nome>` — chamadas de tools
- `mcp.resource.<uri>` — leituras de resources
- `mcp.prompt.<nome>` — obtenções de prompts

Para que o **trace** tenha um **span raiz por request** (ex.: "POST /mcp") em vez da primeira operação (ex.: Redis SETEX), use o `SolviewMCPASGIMiddleware` como camada mais externa do app ASGI. Na instrumentação FastAPI esse problema não existe: o FastAPIInstrumentor já cria um span raiz por request. Para mais detalhes, veja o [Guia MCP](mcp.md).

⸻

## 🔧 Melhores Práticas
	•	Sempre configure o service_name e service_version para facilitar a identificação dos traces.
	•	Prefira o protocolo gRPC para performance.
	•	Monitore e otimize a coleta de spans para evitar overload em produção.
