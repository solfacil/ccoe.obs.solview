from fastapi import FastAPI
from starlette.testclient import TestClient
from solview.tracing.core import setup_tracer

def test_traceparent_propagation(monkeypatch):
    monkeypatch.setenv("PYTHON_ENV", "unittest")
    app = FastAPI()
    setup_tracer(app=app, service_name="propagate-service")
    
    @app.get("/foo")
    def foo():
        from solview.tracing.propagators import inject_correlation_context
        from opentelemetry.trace import get_tracer
        tracer = get_tracer(__name__)
        with tracer.start_as_current_span("test-span"):
            headers = {}
            inject_correlation_context(headers)
            return headers

    client = TestClient(app)
    response = client.get("/foo")
    # O header traceparent é retornado na resposta
    assert "traceparent" in response.json()