from fastapi import FastAPI
from starlette.testclient import TestClient
from solview.config import setup_settings
from solview.settings import SolviewSettings
from solview.tracing.core import setup_tracer

def test_traceparent_propagation(monkeypatch):
    monkeypatch.setenv("PYTHON_ENV", "unittest")
    app = FastAPI()
    setup_settings(SolviewSettings(service_name="propagate-service", use_console_exporter_on_unittest=True))
    setup_tracer(app=app)
    
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