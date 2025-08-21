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
    "shutdown_tracing",
]

def get_tracer(name: str = __name__):
    return _trace.get_tracer(name)

def shutdown_tracing():
    """Flush/Shutdown dos span processors (para scripts e encerramento limpo)."""
    try:
        provider = _trace.get_tracer_provider()
        # Compatível com SDK default
        processors = getattr(provider, "_active_span_processor", None)
        if processors and hasattr(processors, "_span_processors"):
            for sp in processors._span_processors:
                try:
                    sp.shutdown()
                except Exception:
                    pass
    except Exception:
        pass