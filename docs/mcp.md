# 🤖 Observabilidade MCP com Solview

O módulo **solview.mcp** oferece observabilidade completa para servidores **FastMCP** (v2+), incluindo tracing distribuído, métricas Prometheus e memory profiling — sem modificar a lógica das suas tools.

---

## 🚀 Instalação

```bash
pip install solview[mcp]
```

Isso instala o `solview` junto com o `fastmcp` como dependência.

---

## ⚡ Quick Start

```python
from fastmcp import FastMCP
from prometheus_client import start_http_server
from solview import SolviewSettings, setup_settings, setup_logger, setup_tracer
from solview.mcp import SolviewMCPMiddleware

# 1. Configurar Solview
setup_settings(SolviewSettings(service_name="meu-mcp-server"))
setup_logger()

# 2. Configurar tracing (httpx, asyncpg, sqlalchemy, requests, redis, etc.)
setup_tracer()

# 3. Expor métricas para Prometheus
start_http_server(port=9090)

# 4. Criar servidor MCP com middleware de observabilidade
mcp = FastMCP("MeuServidor")
mcp.add_middleware(SolviewMCPMiddleware())

@mcp.tool
async def buscar_cliente(cpf: str) -> str:
    """Busca dados de um cliente pelo CPF."""
    return f"Cliente com CPF {cpf}"

@mcp.resource("file://{path}")
async def ler_arquivo(path: str) -> str:
    """Lê conteúdo de um arquivo."""
    return open(path).read()

@mcp.prompt
async def resumo(texto: str) -> str:
    """Gera um resumo do texto."""
    return f"Resuma: {texto}"
```

Com isso, cada chamada a `buscar_cliente`, `ler_arquivo` ou `resumo` gera automaticamente:
- Um **span OpenTelemetry** com atributos MCP
- Métricas Prometheus **business_operations_***

---

## 📊 Métricas Geradas

O middleware reutiliza a família de métricas `business_operations_*`, garantindo compatibilidade com dashboards e alertas existentes:

| Métrica | Tipo | Labels | Descrição |
|---------|------|--------|-----------|
| `business_operations_total` | Counter | `operation`, `app_name`, `status` | Total de operações MCP |
| `business_operations_duration_seconds` | Histogram | `operation`, `app_name`, `status` | Duração das operações |
| `business_operations_memory_bytes` | Histogram | `operation`, `app_name`, `status` | Uso de memória (quando habilitado) |
| `business_operations_memory_samples_total` | Counter | `operation`, `app_name` | Amostras de memória coletadas |

### Labels de operação por tipo

| Tipo MCP | Formato do label `operation` | Exemplo |
|----------|------------------------------|---------|
| Tool call | `tool.<nome_da_tool>` | `tool.buscar_cliente` |
| Resource read | `resource.<uri>` | `resource.file:///data.csv` |
| Prompt get | `prompt.<nome_do_prompt>` | `prompt.resumo` |

---

## 📐 Trace name (span raiz por request)

Em servidores MCP expostos via HTTP (ex.: `POST /mcp`), **sem** um span raiz por request, a primeira operação executada (ex.: Redis SETEX do cache) vira a raiz do trace e o nome do trace fica incorreto (ex.: "mcp-distribution SETEX"). Para que o trace tenha um nome correto por request (ex.: "POST /mcp"):

1. **Use o middleware ASGI** `SolviewMCPASGIMiddleware` como **camada mais externa** do app ASGI, antes de qualquer cache ou lógica de negócio. Assim, cada request HTTP gera um span raiz no formato `METHOD path` (ex.: "POST /mcp") e as operações MCP/Redis ficam como filhos desse span.

2. **Como aplicar**: quando seu framework (ex.: FastMCP) expõe o app ASGI, envolva-o com `SolviewMCPASGIMiddleware` antes de passar para o servidor (ex.: uvicorn):

```python
from fastmcp import FastMCP
from solview.mcp import SolviewMCPMiddleware, SolviewMCPASGIMiddleware

mcp = FastMCP("MeuServidor")
mcp.add_middleware(SolviewMCPMiddleware())
app = mcp.get_asgi_app()  # ou como seu framework expõe o app
app = SolviewMCPASGIMiddleware(app)
uvicorn.run(app, host="0.0.0.0", port=8000)
```

**Nota:** Na instrumentação FastAPI (`setup_tracer(app)` com app FastAPI), esse problema **não existe**: o `FastAPIInstrumentor` já cria um span raiz por request HTTP (ex.: "GET /items"), então o nome do trace já reflete o endpoint.

---

## 🔍 Spans OpenTelemetry

Cada operação MCP gera um span com os seguintes atributos:

### Atributos comuns

| Atributo | Descrição |
|----------|-----------|
| `mcp.operation_type` | Tipo: `tool`, `resource` ou `prompt` |
| `mcp.operation_name` | Nome da operação |
| `memory.sampling.enabled` | Se memory profiling está ativo |

### Atributos por tipo

| Tipo | Atributo específico | Exemplo |
|------|---------------------|---------|
| Tool | `mcp.tool.name` | `buscar_cliente` |
| Resource | `mcp.resource.uri` | `file:///data.csv` |
| Prompt | `mcp.prompt.name` | `resumo` |

### Nomes dos spans

- **Span raiz por request** (quando se usa `SolviewMCPASGIMiddleware`): `METHOD path` — ex.: `POST /mcp`.
- **Spans de operação MCP** (gerados por `SolviewMCPMiddleware`): padrão `mcp.<tipo>.<nome>`:
  - `mcp.tool.buscar_cliente`
  - `mcp.resource.file:///data.csv`
  - `mcp.prompt.resumo`

---

## 🔧 setup_tracer() para MCP

A função `setup_tracer()` (de `solview.tracing`) é **unificada** para FastAPI e FastMCP. Quando chamada **sem** o argumento `app`, aplica apenas as auto-instrumentações de biblioteca:

| Instrumentação | Biblioteca | O que captura |
|----------------|-----------|---------------|
| HTTPXClientInstrumentor | `httpx` | Chamadas HTTP async |
| RequestsInstrumentor | `requests` | Chamadas HTTP sync |
| AsyncPGInstrumentor | `asyncpg` | Queries PostgreSQL async |
| SQLAlchemyInstrumentor | `sqlalchemy` | Queries via ORM/SQL |
| LoggingInstrumentor | `logging` | Correlação trace_id nos logs |
| HttpClientInstrumentor | `http.client` | stdlib HTTP |
| RedisInstrumentor | `redis`, `redis.asyncio` | Operações Redis sync e async |

Quando chamada **com** `app` (instância de FastAPI), aplica adicionalmente `FastAPIInstrumentor` e `prometheus-fastapi-instrumentator`.

Isso significa que se sua tool MCP faz chamadas HTTP (httpx/requests), acessa banco de dados (asyncpg/sqlalchemy) ou usa Redis (`redis` e `redis.asyncio`), essas operações serão **automaticamente rastreadas** como child spans.

### Comportamento por contexto

| Funcionalidade | `setup_tracer(app)` | `setup_tracer()` |
|---------------|:---:|:---:|
| TracerProvider + sampler | ✅ | ✅ |
| MeterProvider + Prometheus | ✅ | ✅ |
| OTLP exporter (gRPC/HTTP) | ✅ | ✅ |
| httpx, requests, asyncpg, sqlalchemy, redis | ✅ | ✅ |
| logging (trace_id) | ✅ | ✅ |
| FastAPIInstrumentor | ✅ | — |
| prometheus-fastapi-instrumentator | ✅ | — |

---

## 📡 Expondo /metrics para Prometheus

O FastMCP não possui endpoint HTTP nativo para métricas. Use `prometheus_client.start_http_server` para expor um servidor HTTP dedicado:

```python
from prometheus_client import start_http_server

# Expõe métricas na porta 9090
start_http_server(port=9090)
```

Configure o Prometheus para coletar:

```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'meu-mcp-server'
    static_configs:
      - targets: ['mcp-server:9090']
    scrape_interval: 15s
```

---

## 🧠 Memory Profiling

O memory profiling funciona da mesma forma que nos demais módulos do Solview:

```python
setup_settings(SolviewSettings(
    service_name="meu-mcp-server",
    enable_memory_profiling=True,
    sampling_memory_profiling=0.1,  # 10% das operações
))
```

| Ambiente | Recomendação |
|----------|-------------|
| Local | `1.0` (100%) |
| Staging | `0.1` (10%) |
| Produção | `0.01` (1%) |

---

## 🧪 Testes

Os testes do módulo MCP ficam em `tests/mcp/`:

```bash
# Rodar testes MCP
pytest tests/mcp/ -v

# Com cobertura
pytest tests/mcp/ --cov=solview.mcp -v
```

### Estrutura dos testes

| Arquivo | Cobertura |
|---------|-----------|
| `test_middleware.py` | Tool calls, resource reads, prompt gets (success + error) |
| `test_middleware_memory.py` | Memory profiling habilitado/desabilitado |
| `test_middleware_tracing.py` | Spans, atributos, status OK/ERROR, exception events |
| `test_asgi_middleware.py` | Span raiz por request HTTP (POST /mcp), status e exceções |
| `test_tracing.py` | setup_tracer sem app, instrumentors, unittest mode |

---

## 🎯 Boas Práticas

1. **Sempre chame `setup_settings()` antes** de `setup_tracer()` e do middleware
2. **Use `start_http_server`** para expor métricas — o MCP não tem `/metrics` nativo
3. **Nomeie suas tools de forma descritiva** — o nome vira label `operation` nas métricas
4. **Configure sampling de memória** adequado ao ambiente (produção: 1%)
5. **Use `setup_tracer()` sem app** — a mesma função funciona para FastAPI e FastMCP
6. **Use `SolviewMCPASGIMiddleware`** como camada mais externa do app ASGI para que o trace tenha nome por request (ex.: "POST /mcp") em vez da primeira operação (ex.: Redis SETEX)

---

<div align="center">

**🤖 Observabilidade completa para servidores MCP**

[🏠 Home](../README.md) | [📚 Docs](README.md) | [📋 Instrumentação](instrumentation-guide.md)

</div>
