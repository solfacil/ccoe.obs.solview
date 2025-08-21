"""
🏗️ Application Builder - Integrado com Solview

Builder para criar e configurar a aplicação FastAPI usando a biblioteca Solview.
"""

from typing import Optional, AsyncContextManager

from fastapi import FastAPI
from solview import get_logger
from opentelemetry.trace import get_current_span

from app.application.rest.catalog import router as catalog_router
from app.application.rest.order import router as order_router
from app.application.rest.health import router as health_router
from app.application.rest.errors import router as errors_router
from app.environment import get_settings


def create_app(
    title: str = "Solview Demo Application",
    description: str = "Demo estruturado do Solview",
    version: str = "1.0.0",
    lifespan: Optional[AsyncContextManager] = None,
    debug: bool = False
) -> FastAPI:
    """
    Cria e configura a aplicação FastAPI integrada com Solview.
    
    Args:
        title: Título da aplicação
        description: Descrição da aplicação
        version: Versão da aplicação
        lifespan: Context manager para ciclo de vida
        debug: Modo debug
        
    Returns:
        FastAPI: Aplicação configurada com Solview
    """
    settings = get_settings()
    
    # Criar aplicação FastAPI
    app = FastAPI(
        title=title,
        description=description,
        version=version,
        lifespan=lifespan,
        debug=debug,
        docs_url="/docs" if settings.is_development else None,
        redoc_url="/redoc" if settings.is_development else None,
        openapi_url="/openapi.json" if settings.is_development else None
    )
    
    # Registrar routers
    _register_routes(app)
    
    logger.info(
        "✅ FastAPI app configurada com Solview",
        title=title,
        version=version,
        event="app_builder_complete"
    )
    
    return app


def _register_routes(app: FastAPI) -> None:
    """
    Registra todas as rotas da aplicação.
    
    Args:
        app: Instância do FastAPI
    """
    settings = get_settings()
    
    # Rotas de observabilidade (sem prefixo)
    app.include_router(health_router, tags=["Observability"])
    
    # Rotas da API (com prefixo)
    api_prefix = settings.api_prefix
    
    app.include_router(
        catalog_router,
        prefix=f"{api_prefix}/catalog",
        tags=["Catalog"]
    )
    
    app.include_router(
        order_router,
        prefix=f"{api_prefix}/orders",
        tags=["Orders"]
    )
    
    # 🐛 Error Simulation Routes
    app.include_router(
        errors_router,
        prefix=f"{api_prefix}/errors",
        tags=["Error Simulation"]
    )
    
    # Rota raiz demonstrando integração Solview
    @app.get("/", tags=["Root"])
    async def root():
        """
        Endpoint raiz demonstrando integração com Solview.
        Mostra trace_id/span_id do OpenTelemetry e logging estruturado.
        """
        # Obter trace context do OpenTelemetry (via Solview)
        try:
            from opentelemetry.trace import format_trace_id, format_span_id
            span = get_current_span()
            trace_id = format_trace_id(span.get_span_context().trace_id)
            span_id = format_span_id(span.get_span_context().span_id)
        except Exception:
            trace_id = "not-available"
            span_id = "not-available"
        
        # Log estruturado via Solview
        logger.info(
            "🌟 Endpoint raiz acessado",
            trace_id=trace_id,
            span_id=span_id,
            endpoint="/",
            method="GET",
            event="root_endpoint_accessed"
        )
        
        response = {
            "message": "🌟 Solview Demo Application",
            "description": "Exemplo de aplicação integrada com Solview",
            "service": settings.service_name,
            "version": settings.version,
            "environment": settings.environment,
            "status": "running",
            "solview_integration": {
                "logging": "✅ Loguru + estruturado",
                "tracing": "✅ OpenTelemetry automático",
                "metrics": "✅ Prometheus middleware",
                "service_graph": "✅ Habilitado via Solview"
            },
            "trace_context": {
                "trace_id": trace_id,
                "span_id": span_id
            },
            "endpoints": {
                "health": "/health",
                "ready": "/ready", 
                "metrics": "/metrics",
                "docs": "/docs" if settings.is_development else None,
                "api": {
                    "catalog": f"{api_prefix}/catalog",
                    "cart": f"{api_prefix}/cart",
                    "orders": f"{api_prefix}/orders"
                }
            }
        }
        
        return response
