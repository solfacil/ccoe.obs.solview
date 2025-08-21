"""
solview.tracing

Módulo de tracing universal, pronto para FastAPI e facilmente extensível para outros frameworks.
"""
from .core import setup_tracer, setup_tracer_from_env
from opentelemetry import trace as _trace
from .propagators import inject_correlation_context, extract_correlation_context

__all__ = [
    "setup_tracer",
    "setup_tracer_from_env",
    "inject_correlation_context",
    "extract_correlation_context",
    "get_tracer",
]

def get_tracer(name: str = __name__):
    return _trace.get_tracer(name)