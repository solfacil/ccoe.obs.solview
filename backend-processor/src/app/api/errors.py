"""
🐛 ERROR SIMULATION ENDPOINTS - Backend Processor
===============================================

Rotas específicas para simular diferentes tipos de erros
para testar Error Rate queries e alertas no backend-processor.
"""

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse
import random
import time
import asyncio
from typing import Dict, Any

from solview import get_logger

router = APIRouter()
logger = get_logger(__name__)

@router.get("/400")
async def simulate_bad_request() -> Dict[str, Any]:
    """Simula erro 400 - Bad Request"""
    logger.warning("Backend: Simulating 400 Bad Request error", 
                  error_type="bad_request", 
                  service="backend-processor",
                  event="error_simulation")
    
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Backend: Bad Request - Invalid parameters for testing"
    )

@router.get("/401") 
async def simulate_unauthorized() -> Dict[str, Any]:
    """Simula erro 401 - Unauthorized"""
    logger.warning("Backend: Simulating 401 Unauthorized error",
                  error_type="unauthorized",
                  service="backend-processor",
                  event="error_simulation")
    
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Backend: Unauthorized - Missing or invalid authentication"
    )

@router.get("/403")
async def simulate_forbidden() -> Dict[str, Any]:
    """Simula erro 403 - Forbidden"""
    logger.warning("Backend: Simulating 403 Forbidden error",
                  error_type="forbidden",
                  service="backend-processor", 
                  event="error_simulation")
    
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Backend: Forbidden - Access denied for testing"
    )

@router.get("/404")
async def simulate_not_found() -> Dict[str, Any]:
    """Simula erro 404 - Not Found"""
    logger.warning("Backend: Simulating 404 Not Found error",
                  error_type="not_found",
                  service="backend-processor",
                  event="error_simulation")
    
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Backend: Not Found - Resource does not exist"
    )

@router.get("/422")
async def simulate_validation_error() -> Dict[str, Any]:
    """Simula erro 422 - Unprocessable Entity"""
    logger.warning("Backend: Simulating 422 Validation error",
                  error_type="validation_error",
                  service="backend-processor",
                  event="error_simulation")
    
    raise HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail="Backend: Unprocessable Entity - Validation failed"
    )

@router.get("/429")
async def simulate_rate_limit() -> Dict[str, Any]:
    """Simula erro 429 - Too Many Requests"""
    logger.warning("Backend: Simulating 429 Rate Limit error",
                  error_type="rate_limit",
                  service="backend-processor",
                  event="error_simulation")
    
    raise HTTPException(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        detail="Backend: Too Many Requests - Rate limit exceeded"
    )

@router.get("/500")
async def simulate_internal_error() -> Dict[str, Any]:
    """Simula erro 500 - Internal Server Error"""
    logger.error("Backend: Simulating 500 Internal Server Error",
                error_type="internal_error",
                service="backend-processor",
                event="error_simulation")
    
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Backend: Internal Server Error - Something went wrong"
    )

@router.get("/502")
async def simulate_bad_gateway() -> Dict[str, Any]:
    """Simula erro 502 - Bad Gateway"""
    logger.error("Backend: Simulating 502 Bad Gateway error",
                error_type="bad_gateway",
                service="backend-processor",
                event="error_simulation")
    
    raise HTTPException(
        status_code=status.HTTP_502_BAD_GATEWAY,
        detail="Backend: Bad Gateway - Upstream server error"
    )

@router.get("/503")
async def simulate_service_unavailable() -> Dict[str, Any]:
    """Simula erro 503 - Service Unavailable"""
    logger.error("Backend: Simulating 503 Service Unavailable error",
                error_type="service_unavailable",
                service="backend-processor",
                event="error_simulation")
    
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="Backend: Service Unavailable - Service temporarily down"
    )

@router.get("/504")
async def simulate_gateway_timeout() -> Dict[str, Any]:
    """Simula erro 504 - Gateway Timeout"""
    logger.error("Backend: Simulating 504 Gateway Timeout error",
                error_type="gateway_timeout",
                service="backend-processor",
                event="error_simulation")
    
    # Simulate slow response before timeout
    await asyncio.sleep(0.1)
    
    raise HTTPException(
        status_code=status.HTTP_504_GATEWAY_TIMEOUT,
        detail="Backend: Gateway Timeout - Upstream server timeout"
    )

@router.get("/random")
async def simulate_random_error() -> Dict[str, Any]:
    """Simula erro aleatório para testes variados"""
    
    error_types = [
        (400, "Bad Request"),
        (401, "Unauthorized"), 
        (403, "Forbidden"),
        (404, "Not Found"),
        (422, "Unprocessable Entity"),
        (429, "Too Many Requests"),
        (500, "Internal Server Error"),
        (502, "Bad Gateway"),
        (503, "Service Unavailable"),
        (504, "Gateway Timeout")
    ]
    
    status_code, error_message = random.choice(error_types)
    
    logger.warning(f"Backend: Simulating random error: {status_code}",
                  error_type="random_error",
                  service="backend-processor",
                  status_code=status_code,
                  event="error_simulation")
    
    raise HTTPException(
        status_code=status_code,
        detail=f"Backend: {error_message} - Random error for testing"
    )

@router.get("/slow")
async def simulate_slow_endpoint() -> Dict[str, Any]:
    """Simula endpoint lento que pode causar timeouts"""
    
    # Random delay between 1-5 seconds
    delay = random.uniform(1.0, 5.0)
    
    logger.info(f"Backend: Simulating slow endpoint with {delay:.2f}s delay",
               delay_seconds=delay,
               service="backend-processor",
               event="slow_simulation")
    
    await asyncio.sleep(delay)
    
    # 20% chance of timing out after delay
    if random.random() < 0.2:
        logger.error("Backend: Slow endpoint timed out",
                    error_type="timeout",
                    service="backend-processor",
                    event="error_simulation")
        
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Backend: Gateway Timeout - Request took too long"
        )
    
    return {
        "message": "Backend: Slow endpoint completed successfully",
        "service": "backend-processor",
        "delay_seconds": delay,
        "timestamp": time.time()
    }

@router.get("/chaos")
async def simulate_chaos() -> Dict[str, Any]:
    """Simula comportamento caótico - pode retornar sucesso ou erro"""
    
    chaos_scenarios = [
        # 30% success
        (0.3, lambda: {
            "message": "Backend: Chaos endpoint succeeded", 
            "service": "backend-processor",
            "chaos": True
        }),
        # 70% various errors
        (0.4, lambda: HTTPException(status_code=500, detail="Backend: Chaos - Internal Error")),
        (0.5, lambda: HTTPException(status_code=503, detail="Backend: Chaos - Service Unavailable")),
        (0.6, lambda: HTTPException(status_code=429, detail="Backend: Chaos - Rate Limited")),
        (0.7, lambda: HTTPException(status_code=502, detail="Backend: Chaos - Bad Gateway")),
    ]
    
    rand = random.random()
    
    for threshold, action in chaos_scenarios:
        if rand <= threshold:
            result = action()
            if isinstance(result, HTTPException):
                logger.warning(f"Backend: Chaos endpoint returning {result.status_code}",
                             error_type="chaos",
                             service="backend-processor",
                             status_code=result.status_code,
                             event="error_simulation")
                raise result
            else:
                logger.info("Backend: Chaos endpoint succeeded",
                           service="backend-processor",
                           event="chaos_success")
                return result
    
    # Fallback success
    return {
        "message": "Backend: Chaos endpoint succeeded", 
        "service": "backend-processor",
        "chaos": True
    }

@router.get("/cascade-error")
async def simulate_cascade_error() -> Dict[str, Any]:
    """Simula erro em cascata - chama demo-app que pode falhar"""
    
    import httpx
    
    logger.info("Backend: Attempting cascade error test",
               service="backend-processor",
               event="cascade_error_start")
    
    try:
        # Tentar chamar uma rota de erro da demo-app
        error_endpoints = ["/api/errors/500", "/api/errors/503", "/api/errors/random"]
        endpoint = random.choice(error_endpoints)
        
        async with httpx.AsyncClient() as client:
            response = await client.get(f"http://solview-demo:8000{endpoint}")
            response.raise_for_status()
            
        logger.info("Backend: Cascade error - demo-app succeeded unexpectedly",
                   service="backend-processor",
                   demo_endpoint=endpoint,
                   event="cascade_error_success")
        
        return {
            "message": "Backend: Cascade error - demo-app succeeded",
            "service": "backend-processor", 
            "demo_endpoint": endpoint,
            "cascade": True
        }
        
    except httpx.RequestError as e:
        logger.error("Backend: Cascade error - network failure",
                    error_type="cascade_network_error",
                    service="backend-processor",
                    error=str(e),
                    event="error_simulation")
        
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Backend: Cascade error - Network failure: {str(e)}"
        )
        
    except httpx.HTTPStatusError as e:
        logger.warning("Backend: Cascade error - demo-app returned error as expected",
                      error_type="cascade_http_error",
                      service="backend-processor", 
                      demo_status_code=e.response.status_code,
                      event="cascade_error_expected")
        
        # Propagar o erro com contexto adicional
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"Backend: Cascade error - Demo-app returned {e.response.status_code}"
        )
