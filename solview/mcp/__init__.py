"""
solview.mcp

Módulo de observabilidade para FastMCP (v2+).
Fornece middleware para instrumentar servidores MCP com tracing OpenTelemetry
e métricas Prometheus, reutilizando a família de métricas business_operations_*.

Instalação: pip install solview[mcp]
"""

from .middleware import SolviewMCPMiddleware
from .tracing import setup_mcp_tracer

__all__ = [
    "SolviewMCPMiddleware",
    "setup_mcp_tracer",
]
