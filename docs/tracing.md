# 🔍 Tracing Distribuído com Solview

O módulo solview.tracing fornece tracing distribuído simples e eficiente usando o OpenTelemetry, facilitando a integração com FastAPI e outras aplicações Python modernas.

⸻

## 🚀 Integração Rápida

Exemplo básico para integrar tracing em uma aplicação FastAPI:

```python
from fastapi import FastAPI
from solview.tracing import setup_tracer

app = FastAPI()
setup_tracer(app)
```

Este setup inicializa automaticamente o tracing baseado em variáveis de ambiente padrão.

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

## 🤖 Tracing para MCP (FastMCP)

Para servidores FastMCP (v2+), use o mesmo `setup_tracer()` — basta chamá-lo **sem** o argumento `app`:

```python
from solview import SolviewSettings, setup_settings, setup_tracer
from solview.mcp import SolviewMCPMiddleware

setup_settings(SolviewSettings(service_name="meu-mcp-server"))
setup_tracer()
```

Quando `app` não é passado (ou é `None`), o `setup_tracer()` configura o TracerProvider e ativa as auto-instrumentações de biblioteca (httpx, requests, asyncpg, sqlalchemy, redis, logging), sem aplicar instrumentação específica de FastAPI.

O `SolviewMCPMiddleware` gera spans para cada operação MCP:
- `mcp.tool.<nome>` — chamadas de tools
- `mcp.resource.<uri>` — leituras de resources
- `mcp.prompt.<nome>` — obtenções de prompts

Para mais detalhes, veja o [Guia MCP](mcp.md).

⸻

## 🔧 Melhores Práticas
	•	Sempre configure o service_name e service_version para facilitar a identificação dos traces.
	•	Prefira o protocolo gRPC para performance.
	•	Monitore e otimize a coleta de spans para evitar overload em produção.
