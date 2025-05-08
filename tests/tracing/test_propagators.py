from solview.tracing.propagators import inject_correlation_context, extract_correlation_context
from opentelemetry.trace import get_tracer

def test_inject_correlation_context():
    tracer = get_tracer(__name__)
    with tracer.start_as_current_span("test-span"):
        headers = {}
        inject_correlation_context(headers)
        # Deve injetar traceparent
        assert any(k.lower() == "traceparent" for k in headers.keys())

def test_extract_correlation_context():
    headers = {}
    inject_correlation_context(headers)
    span = extract_correlation_context(headers)
    # Deve retornar um objeto Span, e o contexto deve ter trace_id
    ctx = span.get_span_context()
    assert hasattr(ctx, "trace_id")
    assert ctx.trace_id is not None