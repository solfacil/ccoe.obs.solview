"""
🐛 ERROR SIMULATION ENDPOINTS
============================

Rotas específicas para simular diferentes tipos de erros
para testar Error Rate queries e alertas.
"""

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse
import random
import time
from typing import Dict, Any

from solview import get_logger
logger = get_logger(__name__)

router = APIRouter()

@router.get("/400")
async def simulate_bad_request() -> Dict[str, Any]:
    """Simula erro 400 - Bad Request"""
    logger.warning("Simulating 400 Bad Request error", 
                  error_type="bad_request", 
                  event="error_simulation")
    
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Bad Request - Invalid parameters for testing"
    )

@router.get("/401") 
async def simulate_unauthorized() -> Dict[str, Any]:
    """Simula erro 401 - Unauthorized"""
    logger.warning("Simulating 401 Unauthorized error",
                  error_type="unauthorized",
                  event="error_simulation")
    
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Unauthorized - Missing or invalid authentication"
    )

@router.get("/403")
async def simulate_forbidden() -> Dict[str, Any]:
    """Simula erro 403 - Forbidden"""
    logger.warning("Simulating 403 Forbidden error",
                  error_type="forbidden", 
                  event="error_simulation")
    
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Forbidden - Access denied for testing"
    )

@router.get("/404")
async def simulate_not_found() -> Dict[str, Any]:
    """Simula erro 404 - Not Found"""
    logger.warning("Simulating 404 Not Found error",
                  error_type="not_found",
                  event="error_simulation")
    
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Not Found - Resource does not exist"
    )

@router.get("/422")
async def simulate_validation_error() -> Dict[str, Any]:
    """Simula erro 422 - Unprocessable Entity"""
    logger.warning("Simulating 422 Validation error",
                  error_type="validation_error",
                  event="error_simulation")
    
    raise HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail="Unprocessable Entity - Validation failed"
    )

@router.get("/429")
async def simulate_rate_limit() -> Dict[str, Any]:
    """Simula erro 429 - Too Many Requests"""
    logger.warning("Simulating 429 Rate Limit error",
                  error_type="rate_limit",
                  event="error_simulation")
    
    raise HTTPException(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        detail="Too Many Requests - Rate limit exceeded"
    )

@router.get("/500")
async def simulate_internal_error() -> Dict[str, Any]:
    """Simula erro 500 - Internal Server Error"""
    logger.error("Simulating 500 Internal Server Error",
                error_type="internal_error",
                event="error_simulation")
    
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Internal Server Error - Something went wrong"
    )

@router.get("/502")
async def simulate_bad_gateway() -> Dict[str, Any]:
    """Simula erro 502 - Bad Gateway"""
    logger.error("Simulating 502 Bad Gateway error",
                error_type="bad_gateway",
                event="error_simulation")
    
    raise HTTPException(
        status_code=status.HTTP_502_BAD_GATEWAY,
        detail="Bad Gateway - Upstream server error"
    )

@router.get("/503")
async def simulate_service_unavailable() -> Dict[str, Any]:
    """Simula erro 503 - Service Unavailable"""
    logger.error("Simulating 503 Service Unavailable error",
                error_type="service_unavailable",
                event="error_simulation")
    
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="Service Unavailable - Service temporarily down"
    )

@router.get("/504")
async def simulate_gateway_timeout() -> Dict[str, Any]:
    """Simula erro 504 - Gateway Timeout"""
    logger.error("Simulating 504 Gateway Timeout error",
                error_type="gateway_timeout",
                event="error_simulation")
    
    # Simulate slow response before timeout
    await asyncio.sleep(0.1)
    
    raise HTTPException(
        status_code=status.HTTP_504_GATEWAY_TIMEOUT,
        detail="Gateway Timeout - Upstream server timeout"
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
    
    logger.warning(f"Simulating random error: {status_code}",
                  error_type="random_error",
                  status_code=status_code,
                  event="error_simulation")
    
    raise HTTPException(
        status_code=status_code,
        detail=f"{error_message} - Random error for testing"
    )

@router.get("/slow")
async def simulate_slow_endpoint() -> Dict[str, Any]:
    """Simula endpoint lento que pode causar timeouts"""
    
    # Random delay between 1-5 seconds
    delay = random.uniform(1.0, 5.0)
    
    logger.info(f"Simulating slow endpoint with {delay:.2f}s delay",
               delay_seconds=delay,
               event="slow_simulation")
    
    await asyncio.sleep(delay)
    
    # 20% chance of timing out after delay
    if random.random() < 0.2:
        logger.error("Slow endpoint timed out",
                    error_type="timeout",
                    event="error_simulation")
        
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Gateway Timeout - Request took too long"
        )
    
    return {
        "message": "Slow endpoint completed successfully",
        "delay_seconds": delay,
        "timestamp": time.time()
    }

@router.get("/chaos")
async def simulate_chaos() -> Dict[str, Any]:
    """Simula comportamento caótico - pode retornar sucesso ou erro"""
    
    chaos_scenarios = [
        # 30% success
        (0.3, lambda: {"message": "Chaos endpoint succeeded", "chaos": True}),
        # 70% various errors
        (0.4, lambda: HTTPException(status_code=500, detail="Chaos: Internal Error")),
        (0.5, lambda: HTTPException(status_code=503, detail="Chaos: Service Unavailable")),
        (0.6, lambda: HTTPException(status_code=429, detail="Chaos: Rate Limited")),
        (0.7, lambda: HTTPException(status_code=502, detail="Chaos: Bad Gateway")),
    ]
    
    rand = random.random()
    
    for threshold, action in chaos_scenarios:
        if rand <= threshold:
            result = action()
            if isinstance(result, HTTPException):
                logger.warning(f"Chaos endpoint returning {result.status_code}",
                             error_type="chaos",
                             status_code=result.status_code,
                             event="error_simulation")
                raise result
            else:
                logger.info("Chaos endpoint succeeded",
                           event="chaos_success")
                return result
    
    # Fallback success
    return {"message": "Chaos endpoint succeeded", "chaos": True}

# Import asyncio for sleep functions
import asyncio
