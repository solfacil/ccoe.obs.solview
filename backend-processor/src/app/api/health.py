"""
❤️ Health Check Endpoints - Backend Processor

Health endpoints integrated with Solview for observability.
"""

import time
from typing import Dict, Any

from fastapi import APIRouter, HTTPException, Depends
from solview import get_logger
logger = get_logger(__name__)
from opentelemetry import trace
from opentelemetry.trace import get_current_span, format_trace_id, format_span_id

from app.environment import get_settings, Settings
from app.services.demo_client import DemoAppClient

router = APIRouter()


@router.get("/health")
async def health_check(settings: Settings = Depends(get_settings)) -> Dict[str, Any]:
    """
    Health check for Backend Processor with service dependency check.
    
    Returns:
        Dict: Health status with service dependencies
    """
    start_time = time.time()
    
    # Get trace context from OpenTelemetry (via Solview)
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
            "solview_integration": "ok",
            "demo_app_connectivity": "checking..."
        }
    }
    
    # Check Demo App connectivity
    try:
        demo_client = DemoAppClient(settings)
        demo_health = await demo_client.check_health()
        
        if demo_health and demo_health.get("status") == "healthy":
            health_data["checks"]["demo_app_connectivity"] = "ok"
            health_data["dependencies"] = {
                "demo_app": {
                    "status": "healthy",
                    "url": settings.demo_app_url,
                    "version": demo_health.get("version", "unknown")
                }
            }
        else:
            health_data["status"] = "degraded"
            health_data["checks"]["demo_app_connectivity"] = "unavailable"
            health_data["dependencies"] = {
                "demo_app": {
                    "status": "unavailable",
                    "url": settings.demo_app_url
                }
            }
    except Exception as e:
        health_data["status"] = "degraded"
        health_data["checks"]["demo_app_connectivity"] = f"error: {str(e)}"
        health_data["dependencies"] = {
            "demo_app": {
                "status": "error",
                "url": settings.demo_app_url,
                "error": str(e)
            }
        }
    
    # Verify critical configurations
    if not settings.service_name:
        health_data["status"] = "unhealthy"
        health_data["checks"]["configuration"] = "missing_service_name"
    
    duration = time.time() - start_time
    
    # Structured logging via Solview
    logger.info(
        "❤️ Health check performed",
        status=health_data["status"],
        duration_ms=duration * 1000,
        trace_id=trace_id,
        span_id=span_id,
        demo_app_status=health_data["checks"]["demo_app_connectivity"],
        event="health_check_performed"
    )
    
    if health_data["status"] == "unhealthy":
        logger.error(
            "❌ Health check failed",
            status=health_data["status"],
            checks=health_data["checks"],
            event="health_check_failed"
        )
        raise HTTPException(status_code=503, detail=health_data)
    
    return health_data


@router.get("/ready")
async def readiness_check(settings: Settings = Depends(get_settings)) -> Dict[str, Any]:
    """
    Readiness check for Kubernetes.
    
    Returns:
        Dict: Readiness status
    """
    tracer = trace.get_tracer(__name__)
    
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
        
        # Check observability features
        if settings.otel_enabled:
            readiness_data["checks"]["opentelemetry"] = "ready"
        
        if settings.metrics_enabled:
            readiness_data["checks"]["prometheus"] = "ready"
            
        if settings.service_graph_enabled:
            readiness_data["checks"]["service_graph"] = "ready"
        
        duration = time.time() - start_time
        span.set_attribute("health.check_duration_ms", duration * 1000)
        
        logger.info(
            "Readiness check performed",
            status=readiness_data["status"],
            duration_ms=duration * 1000,
            event="readiness_check"
        )
        
        return readiness_data


@router.get("/info")
async def application_info(settings: Settings = Depends(get_settings)) -> Dict[str, Any]:
    """
    Detailed application information.
    
    Returns:
        Dict: Application information
    """
    tracer = trace.get_tracer(__name__)
    
    with tracer.start_as_current_span("application_info") as span:
        span.set_attribute("service.name", settings.service_name)
        
        return {
            "service": {
                "name": settings.service_name,
                "version": settings.version,
                "environment": settings.environment,
                "debug": settings.debug,
                "port": settings.port
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
                "cors_origins": settings.cors_origins,
                "batch_size": settings.batch_size,
                "processing_interval": settings.processing_interval
            },
            "dependencies": {
                "demo_app": {
                    "url": settings.demo_app_url,
                    "timeout": settings.demo_app_timeout
                }
            },
            "architecture": {
                "pattern": "microservice",
                "communication": "http",
                "observability_stack": "LGTM",
                "purpose": "service_graph_generation"
            }
        }
