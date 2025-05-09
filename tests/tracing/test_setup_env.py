import os
from fastapi import FastAPI
from solview.tracing.core import setup_tracer

def test_setup_tracer(monkeypatch):
    monkeypatch.setenv("OTEL_EXPORTER_OTLP_ENDPOINT", "tracetesthost")
    monkeypatch.setenv("OTEL_EXPORTER_OTLP_ENDPOINT_PORT", "55680")
    monkeypatch.setenv("OTEL_EXPORTER_OTLP_PROTOCOL", "grpc")
    monkeypatch.setenv("PYTHON_ENV", "unittest")
    app = FastAPI()
    provider = setup_tracer(app)
    assert provider is not None
    # Deve configurar otlp exporter (no modo unittest pode ser só ConsoleSpanExporter)