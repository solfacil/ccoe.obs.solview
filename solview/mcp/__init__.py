"""
solview.mcp

Módulo de observabilidade para FastMCP (v2+).
Fornece middleware para instrumentar servidores MCP com tracing OpenTelemetry
e métricas Prometheus, reutilizando a família de métricas business_operations_*.

Para tracing, use ``solview.tracing.setup_tracer()`` (sem app) — funciona
tanto para FastAPI quanto para FastMCP.

Instalação: pip install solview[mcp]
"""

from .asgi_middleware import SolviewMCPASGIMiddleware
from .middleware import SolviewMCPMiddleware

__all__ = [
    "SolviewMCPASGIMiddleware",
    "SolviewMCPMiddleware",
]
