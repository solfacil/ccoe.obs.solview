import pytest
from fastapi import FastAPI
from fastapi.responses import PlainTextResponse
from starlette.testclient import TestClient
from solview.metrics.exporters import SolviewPrometheusMiddleware, prometheus_metrics_response
from solview.metrics.core import METRIC_REQUESTS, METRIC_RESPONSES
from unittest.mock import patch, MagicMock

@pytest.fixture
def app():
    app = FastAPI()
    app.add_middleware(SolviewPrometheusMiddleware, service_name="test-service")

    @app.get("/ping")
    def ping():
        return PlainTextResponse("pong")

    # Endpoint Prometheus
    app.add_route("/metrics", prometheus_metrics_response)
    return app

def test_ping_and_metrics_endpoint(app):
    client = TestClient(app)
    
    # Antes da chamada, captura a contagem da métrica
    before = METRIC_REQUESTS.labels(method="GET", path="/ping", service_name="test-service")._value.get()

    # Faz uma chamada para o endpoint /ping
    resp = client.get("/ping")
    assert resp.status_code == 200
    assert resp.text == "pong"

    # Após chamada, a métrica deve ser incrementada
    after = METRIC_REQUESTS.labels(method="GET", path="/ping", service_name="test-service")._value.get()
    assert after == before + 1

    # Checa se /metrics retorna métricas Prometheus
    metrics_resp = client.get("/metrics")
    assert metrics_resp.status_code == 200
    assert "fastapi_requests_total" in metrics_resp.text
    assert "test-service" in metrics_resp.text

def test_404_path_is_not_counted(app):
    client = TestClient(app)
    resp = client.get("/notfound")
    assert resp.status_code == 404
    # Não incrementa para o path desconhecido, pois get_path_template retorna is_handled_path=False
