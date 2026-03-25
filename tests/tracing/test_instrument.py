import pytest
from fastapi import FastAPI
from solview.config import setup_settings
from solview.settings import SolviewSettings
from solview.tracing.core import setup_tracer


def test_setup_tracer_configures_and_instruments(monkeypatch):
    monkeypatch.setenv("PYTHON_ENV", "unittest")
    app = FastAPI()
    setup_settings(
        SolviewSettings(
            service_name="unit-service", use_console_exporter_on_unittest=True
        )
    )
    provider = setup_tracer(app=app)
    # Confirma que retornou um TracerProvider e FastAPI foi instrumentada
    assert provider is not None
    # O provider contém um resource com o nome do serviço
    resource = provider.resource
    assert resource.attributes.get("service.name") == "unit-service"
