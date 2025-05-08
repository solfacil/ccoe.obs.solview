import os
from fastapi import FastAPI
from solview.tracing.core import setup_tracer_from_env

def test_setup_tracer_from_env(monkeypatch):
    monkeypatch.setenv("OTEL_EXPORTER_OTLP_ENDPOINT_HOST", "tracetesthost")
    monkeypatch.setenv("OTEL_EXPORTER_OTLP_ENDPOINT_PORT", "55680")
    monkeypatch.setenv("OTEL_EXPORTER_OTLP_PROTOCOL", "grpc")
    monkeypatch.setenv("PYTHON_ENV", "unittest")
    app = FastAPI()
    provider = setup_tracer_from_env(app)
    assert provider is not None
    # Deve configurar otlp exporter (no modo unittest pode ser só ConsoleSpanExporter)