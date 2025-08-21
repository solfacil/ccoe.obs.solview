"""
🔧 Backend Processor FastAPI Server

Servidor principal que demonstra comunicação entre serviços
para gerar service graph rico no Grafana.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from solview import get_logger

# Solview imports
from solview.settings import SolviewSettings
from solview.solview_logging import setup_logger
from solview.metrics import SolviewPrometheusMiddleware, prometheus_metrics_response
from solview.tracing import setup_tracer

from app.environment import get_settings
from app.api import health, analytics, processor, errors


# Module-level logger for lifespan and startup logs
logger = get_logger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Lifecycle management for Backend Processor.
    
    Args:
        app: FastAPI instance
    """
    settings = get_settings()
    
    logger.info(
        "🔧 Backend Processor started",
        service=settings.service_name,
        version=settings.version,
        environment=settings.environment,
        demo_app_url=settings.demo_app_url,
        event="startup"
    )
    
    yield
    
    logger.info(
        "🛑 Backend Processor shutting down",
        service=settings.service_name,
        event="shutdown"
    )


def create_application() -> FastAPI:
    logger = get_logger(__name__)
    """
    Create and configure FastAPI application with Solview integration.
    
    Returns:
        FastAPI: Configured application
    """
    settings = get_settings()
    
    # Configure Solview Settings
    solview_settings = SolviewSettings(
        service_name=settings.service_name,
        version=settings.version,
        environment=settings.environment,
        log_level=settings.log_level,
        otlp_exporter_host=settings.otel_endpoint_host,
        otlp_exporter_port=4317,
        otlp_exporter_protocol="grpc"
    )
    
    # 1. Setup Solview Structured Logger
    setup_logger(solview_settings)
    
    # 2. Create FastAPI app
    app = FastAPI(
        title="Backend Processor",
        description="🔧 Service for processing data and generating service graph",
        version=settings.version,
        lifespan=lifespan,
        debug=settings.debug,
        openapi_url=f"{settings.api_prefix}/openapi.json" if settings.debug else None,
        docs_url=f"{settings.api_prefix}/docs" if settings.debug else None,
        redoc_url=f"{settings.api_prefix}/redoc" if settings.debug else None,
    )
    
    # 3. Add Solview Prometheus Metrics Middleware
    app.add_middleware(SolviewPrometheusMiddleware, service_name=settings.service_name)
    
    # 4. Add Solview Metrics Endpoint
    app.add_route("/metrics", prometheus_metrics_response)
    
    # 5. Setup OpenTelemetry Tracing
    setup_tracer(
        app=app,
        service_name=settings.service_name,
        service_version=settings.version,
        otlp_exporter_host=solview_settings.otlp_exporter_host,
        otlp_exporter_port=solview_settings.otlp_exporter_port,
        otlp_exporter_protocol=solview_settings.otlp_exporter_protocol
    )
    
    # 6. Configure CORS
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
    
    # 7. Include API routers
    app.include_router(health.router, tags=["Health"], prefix="")
    
    app.include_router(
        analytics.router,
        tags=["Analytics"],
        prefix=f"{settings.api_prefix}/analytics"
    )
    
    app.include_router(
        processor.router,
        tags=["Processor"],
        prefix=f"{settings.api_prefix}/processor"
    )
    
    # 🐛 Error Simulation Routes
    app.include_router(
        errors.router,
        tags=["Error Simulation"],
        prefix=f"{settings.api_prefix}/errors"
    )
    
    logger.info(
        "✅ Backend Processor initialized with Solview",
        service=settings.service_name,
        features=["logging", "metrics", "tracing", "service_graph"],
        demo_app_url=settings.demo_app_url,
        event="solview_setup_complete"
    )
    
    return app


# Create application instance
app = create_application()
