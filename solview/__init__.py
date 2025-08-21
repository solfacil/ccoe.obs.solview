"""
solview - Observabilidade clara como o Sol ☀️

Biblioteca centralizada de logging, métricas e tracing (Solfácil).
"""
__version__ = "1.0.1"

from .settings import SolviewSettings
from .solview_logging import setup_logger, get_logger
from .tracing import setup_tracer, get_tracer

__all__ = [
    "SolviewSettings",
    "setup_logger",
    "get_logger",
    "setup_tracer",
    "get_tracer",
]