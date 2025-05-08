import pytest
from fastapi import FastAPI
from starlette.testclient import TestClient
from solview.metrics.exporters import SolviewPrometheusMiddleware, prometheus_metrics_response

@pytest.fixture
def app_with_exception():
    app = FastAPI()
    app.add_middleware(SolviewPrometheusMiddleware, service_name="fail-test")
    @app.get("/fail")
    def fail():
        raise RuntimeError("fail")
    app.add_route("/metrics", prometheus_metrics_response)
    return app

def test_exception_metric_and_500_captured(app_with_exception):
    client = TestClient(app_with_exception)
    with pytest.raises(RuntimeError):
        client.get("/fail")
    metrics = client.get("/metrics").text
    assert "fastapi_exceptions_total" in metrics
    # Confirma que exception_type=RuntimeError está presente
    assert 'exception_type="RuntimeError"' in metrics