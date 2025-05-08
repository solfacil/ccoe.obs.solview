import pytest
import asyncio
from fastapi import FastAPI
from solview.metrics.exporters import SolviewPrometheusMiddleware, prometheus_metrics_response
from solview.solview_logging.settings import LoggingSettings

@pytest.fixture
def logging_settings_env(monkeypatch):
    monkeypatch.setenv("SERVICE_NAME", "my-service")
    monkeypatch.setenv("ENVIRONMENT", "staging")
    return LoggingSettings()

@pytest.fixture
def app():
    app = FastAPI()
    app.add_middleware(SolviewPrometheusMiddleware, service_name="test-app")
    @app.get("/ping")
    def ping():
        return {"pong": True}
    app.add_route("/metrics", prometheus_metrics_response)
    return app


@pytest.fixture(scope="session")
def anyio_backend():
    # Faz com que pytest-anyio use sempre asyncio (compatível com pytest-asyncio)
    return "asyncio"

@pytest.fixture(autouse=True, scope="function")
def force_event_loop():
    """
    Garante que cada teste tem um event loop disponível (especialmente onde se inicializa loggers async).
    """
    loop = None
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    yield
    if loop and not loop.is_closed():
        loop.close()