from fastapi import FastAPI
from starlette.testclient import TestClient
from solview.metrics.exporters import SolviewPrometheusMiddleware, prometheus_metrics_response
from solview.metrics.core import METRIC_EXCEPTIONS
import pytest

@pytest.fixture
def app_with_exception():
    app = FastAPI()
    app.add_middleware(SolviewPrometheusMiddleware, service_name="exc-service")

    @app.get("/error")
    def error():
        raise ValueError("Ops")

    app.add_route("/metrics", prometheus_metrics_response)
    return app

def test_exception_metric_increment(app_with_exception):
    client = TestClient(app_with_exception)
    before = METRIC_EXCEPTIONS.labels(method="GET", path="/error", exception_type="ValueError", service_name="exc-service")._value.get()

    with pytest.raises(ValueError):
        client.get("/error")

    after = METRIC_EXCEPTIONS.labels(method="GET", path="/error", exception_type="ValueError", service_name="exc-service")._value.get()
    assert after == before + 1