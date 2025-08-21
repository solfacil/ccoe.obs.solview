"""
❤️ Health Check Endpoints - Integrado com Solview

Endpoints para verificação de saúde da aplicação usando Solview.
"""

import time
from typing import Dict, Any

from fastapi import APIRouter, HTTPException, Depends
from solview import get_logger
logger = get_logger(__name__)
from opentelemetry import trace
from opentelemetry.trace import get_current_span, format_trace_id, format_span_id

from app.environment import get_settings, Settings

router = APIRouter()


@router.get("/health")
async def health_check(settings: Settings = Depends(get_settings)) -> Dict[str, Any]:
    """
    Health check da aplicação integrada com Solview.
    Demonstra tracing automático e logging estruturado.
    
    Returns:
        Dict: Status de saúde da aplicação
    """
    start_time = time.time()
    
    # Obter trace context do OpenTelemetry (via Solview)
    try:
        span = get_current_span()
        trace_id = format_trace_id(span.get_span_context().trace_id)
        span_id = format_span_id(span.get_span_context().span_id)
    except Exception:
        trace_id = "not-available"
        span_id = "not-available"
    
    health_data = {
        "service": settings.service_name,
        "version": settings.version,
        "status": "healthy",
        "timestamp": time.time(),
        "environment": settings.environment,
        "solview_status": {
            "logging": "✅ active",
            "tracing": "✅ active", 
            "metrics": "✅ active"
        },
        "trace_context": {
            "trace_id": trace_id,
            "span_id": span_id
        },
        "checks": {
            "application": "ok",
            "configuration": "ok",
            "solview_integration": "ok"
        }
    }
    
    # Verificar configurações críticas
    if not settings.service_name:
        health_data["status"] = "unhealthy"
        health_data["checks"]["configuration"] = "missing_service_name"
    
    duration = time.time() - start_time
    
    # Log estruturado via Solview
    logger.info(
        "❤️ Health check realizado",
        status=health_data["status"],
        duration_ms=duration * 1000,
        trace_id=trace_id,
        span_id=span_id,
        event="health_check_performed"
    )
    
    if health_data["status"] != "healthy":
        logger.error(
            "❌ Health check falhou",
            status=health_data["status"],
            checks=health_data["checks"],
            event="health_check_failed"
        )
        raise HTTPException(status_code=503, detail=health_data)
    
    return health_data


@router.get("/ready")
async def readiness_check(settings: Settings = Depends(get_settings)) -> Dict[str, Any]:
    """
    Readiness check para Kubernetes.
    
    Returns:
        Dict: Status de prontidão da aplicação
    """
    with tracer.start_as_current_span("readiness_check") as span:
        span.set_attribute("service.name", settings.service_name)
        span.set_attribute("health.check_type", "readiness")
        
        start_time = time.time()
        
        readiness_data = {
            "service": settings.service_name,
            "status": "ready",
            "timestamp": time.time(),
            "checks": {
                "application": "ready",
                "observability": "ready"
            }
        }
        
        # Verificar observabilidade
        if settings.otel_enabled:
            readiness_data["checks"]["opentelemetry"] = "ready"
        
        if settings.metrics_enabled:
            readiness_data["checks"]["prometheus"] = "ready"
        
        duration = time.time() - start_time
        span.set_attribute("health.check_duration_ms", duration * 1000)
        
        logger.info(
            "Readiness check performed",
            extra={
                "extra_fields": {
                    "status": readiness_data["status"],
                    "duration_ms": duration * 1000,
                    "event": "readiness_check"
                }
            }
        )
        
        return readiness_data


@router.get("/info")
async def application_info(settings: Settings = Depends(get_settings)) -> Dict[str, Any]:
    """
    Informações detalhadas da aplicação.
    
    Returns:
        Dict: Informações da aplicação
    """
    with tracer.start_as_current_span("application_info") as span:
        span.set_attribute("service.name", settings.service_name)
        
        return {
            "service": {
                "name": settings.service_name,
                "version": settings.version,
                "environment": settings.environment,
                "debug": settings.debug
            },
            "observability": {
                "opentelemetry_enabled": settings.otel_enabled,
                "service_graph_enabled": settings.service_graph_enabled,
                "metrics_enabled": settings.metrics_enabled,
                "tracing_enabled": settings.tracing_enabled,
                "logging_enabled": settings.logging_enabled,
                "otel_endpoint": settings.otel_exporter_endpoint
            },
            "configuration": {
                "log_level": settings.log_level,
                "api_prefix": settings.api_prefix,
                "cors_origins": settings.cors_origins
            },
            "architecture": {
                "pattern": "hexagonal",
                "layers": ["domain", "application", "infrastructure"],
                "observability_stack": "LGTM"
            }
        }
