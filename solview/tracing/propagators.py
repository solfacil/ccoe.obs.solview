from typing import Any, Dict
from opentelemetry.propagate import inject, extract
from opentelemetry.trace import Span, get_current_span

def inject_correlation_context(headers: Dict[str, str]) -> None:
    """
    Injeta contexto de tracing/correlation nos headers HTTP para chamada downstream.
    """
    inject(headers)
    # Exemplo: headers agora contém traceparent, tracestate, baggage

def extract_correlation_context(headers: Dict[str, Any]) -> Span:
    """
    Extrai contexto de tracing/correlation de headers HTTP recebidos.
    Útil para identificar span/trace_id em middlewares customizados.
    """
    carrier = dict(headers)
    ctx = extract(carrier)
    return get_current_span(ctx)