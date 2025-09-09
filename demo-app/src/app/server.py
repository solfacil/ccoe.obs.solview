"""
🚀 FastAPI Server - Integrado com Solview

Servidor principal da aplicação demonstrando como integrar
a biblioteca Solview para observabilidade completa.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from solview import SolviewSettings, setup_logger, setup_tracer, get_logger
from solview.metrics import SolviewPrometheusMiddleware, prometheus_metrics_response

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Gerencia o ciclo de vida da aplicação.
    
    Args:
        app: Instância do FastAPI
    """
    settings = SolviewSettings(service_name="solview-demo-app")
    
    logger.info(
        "🚀 Solview Demo Application started",
        service=settings.service_name,
        version=settings.version,
        environment=settings.environment,
        event="startup"
    )
    
    yield
    
    logger.info(
        "🛑 Solview Demo Application shutting down",
        service=settings.service_name,
        event="shutdown"
    )


def create_application() -> FastAPI:
    """
    Cria e configura a aplicação FastAPI com Solview integrado.
    
    Returns:
        FastAPI: Aplicação configurada com Solview
    """
    settings = SolviewSettings(service_name="solview-demo-app")
    
    # Configurar Solview Settings
    # solview_settings = SolviewSettings(
    #     service_name=settings.service_name,
    #     version=settings.version,
    #     environment=settings.environment,
    #     log_level=settings.log_level,
    #     otlp_exporter_host=settings.otel_exporter_endpoint.replace("http://", "").replace(":4317", ""),
    #     otlp_exporter_port=4317,
    #     otlp_exporter_protocol="grpc"
    # )
    
    # 1. Setup Logger Estruturado do Solview
    setup_logger(settings)
    
    app = FastAPI(title="Solview Demo App")
    
    # 2. Middleware de Métricas Prometheus do Solview
    app.add_middleware(SolviewPrometheusMiddleware, settings=settings)
    
    # 3. Endpoint de Métricas do Solview
    app.add_route("/metrics", prometheus_metrics_response)
    
    # 4. Setup Tracing OpenTelemetry do Solview
    setup_tracer(settings, app)
    
    # 5. Configurar CORS
    cors_origins = settings.cors_origins_list
    if cors_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=cors_origins,
            allow_credentials=True,
            allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            allow_headers=["*"],
            expose_headers=["X-Trace-Id", "X-Request-Id"]
        )
    
    logger.info(
        "✅ Solview integrado com sucesso",
        service=settings.service_name,
        features=["logging", "metrics", "tracing", "service_graph"],
        event="solview_setup_complete"
    )
    
    return app


# Criar instância da aplicação
app = create_application()
