# =============================================================================
# 🐳 SOLVIEW DEMO APP - MULTI-STAGE DOCKERFILE
# =============================================================================
# Dockerfile otimizado para produção com:
# - Multi-stage build para reduzir tamanho da imagem
# - Non-root user para segurança
# - Cache otimizado para dependências
# - OpenTelemetry e Solview integrados
# =============================================================================

# -----------------------------------------------------------------------------
# 🔧 STAGE 1: BUILDER
# -----------------------------------------------------------------------------
FROM python:3.11-slim as builder

# Instalar dependências de build
RUN apt-get update && apt-get install -y \
    --no-install-recommends \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Criar ambiente virtual
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Atualizar pip e setuptools
RUN pip install --upgrade pip setuptools wheel

# Copiar arquivos de dependência
WORKDIR /build
COPY pyproject.toml ./

# Instalar dependências Python para integração com Solview
RUN pip install fastapi uvicorn pydantic pydantic-settings loguru httpx && \
    pip install opentelemetry-api opentelemetry-sdk \
    opentelemetry-exporter-otlp-proto-grpc \
    opentelemetry-instrumentation-fastapi \
    opentelemetry-instrumentation-requests \
    opentelemetry-instrumentation-logging \
    opentelemetry-instrumentation-asyncpg \
    opentelemetry-instrumentation-sqlalchemy \
    opentelemetry-instrumentation-httpx \
    prometheus-client psycopg2-binary

# -----------------------------------------------------------------------------
# 🚀 STAGE 2: RUNTIME
# -----------------------------------------------------------------------------
FROM python:3.11-slim as runtime

# Metadados
LABEL maintainer="CCOE Platform Team <platform@company.com>"
LABEL description="Solview Demo Application - Structured Observability"
LABEL version="1.0.0"

# Instalar dependências de runtime
RUN apt-get update && apt-get install -y \
    --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Criar usuário não-root
RUN groupadd --gid 1001 solview && \
    useradd --uid 1001 --gid 1001 --shell /bin/bash --create-home solview

# Copiar ambiente virtual do builder
COPY --from=builder /opt/venv /opt/venv

# Configurar PATH
ENV PATH="/opt/venv/bin:$PATH"
ENV PYTHONPATH="/app/src"

# Criar diretório de trabalho
WORKDIR /app

# Copiar código da aplicação demo
COPY --chown=solview:solview ./demo-app/ .

# Copiar e instalar biblioteca Solview do projeto principal
COPY --chown=solview:solview ./solview ./solview_lib/solview
COPY --chown=solview:solview ./pyproject.toml ./solview_lib/
COPY --chown=solview:solview ./requirements.txt ./solview_lib/
RUN pip install -e ./solview_lib/

# Criar diretórios necessários
RUN mkdir -p /app/logs /app/data /app/tmp && \
    chown -R solview:solview /app

# Configurar variáveis de ambiente
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV SOLVIEW_SERVICE_NAME=solview-demo-app
ENV SOLVIEW_VERSION=1.0.0
ENV SOLVIEW_ENVIRONMENT=production
ENV SOLVIEW_LOG_LEVEL=INFO

# OpenTelemetry configuration
ENV OTEL_SERVICE_NAME=solview-demo-app
ENV OTEL_SERVICE_VERSION=1.0.0
ENV OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector:4317
ENV OTEL_RESOURCE_ATTRIBUTES=service.name=solview-demo-app,service.version=1.0.0,service.namespace=solview,deployment.environment=production

# Expor porta
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD ["curl", "-f", "http://localhost:8000/health"]

# Executar como usuário não-root
USER solview

# Comando para iniciar a aplicação
CMD ["python", "-m", "uvicorn", "app.server:app", "--host", "0.0.0.0", "--port", "8000"]
