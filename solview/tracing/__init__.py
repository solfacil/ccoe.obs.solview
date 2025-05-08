"""
solview.tracing

Módulo de tracing universal, pronto para FastAPI e facilmente extensível para outros frameworks.
"""
from .core import setup_tracer, setup_tracer_from_env
from .propagators import inject_correlation_context, extract_correlation_context

__all__ = [
    "setup_tracer",
    "setup_tracer_from_env",
    "inject_correlation_context",
    "extract_correlation_context",
]