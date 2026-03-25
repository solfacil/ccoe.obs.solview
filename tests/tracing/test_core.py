import pytest
from fastapi import FastAPI
from solview.config import setup_settings
from solview.settings import SolviewSettings
from solview.tracing.core import setup_tracer


def test_setup_tracer_configures_provider(monkeypatch):
    # Força ambiente de unittest para usar ConsoleSpanExporter (evita exportar pra fora)
    monkeypatch.setenv("PYTHON_ENV", "unittest")
    app = FastAPI()
    setup_settings(
        SolviewSettings(
            service_name="my-test-service", use_console_exporter_on_unittest=True
        )
    )
    provider = setup_tracer(app=app)
    # O tracer provider deve estar configurado custommente
    assert provider is not None
    # Como foi no modo 'unittest', não deve ter tentado exportador OTLP (logger pode registrar isso)
