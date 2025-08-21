import pytest
from fastapi import FastAPI
from starlette.testclient import TestClient
from solview.metrics.exporters import SolviewPrometheusMiddleware, prometheus_metrics_response

@pytest.fixture
def app():
    app = FastAPI()
    app.add_middleware(SolviewPrometheusMiddleware, service_name="integration-test")
    @app.get("/health")
    def health():
        return {"status": "ok"}
    app.add_route("/metrics", prometheus_metrics_response)
    return app

def test_metrics_are_exposed_and_incremented(app):
    client = TestClient(app)
    # Realiza duas chamadas
    for _ in range(2):
        resp = client.get("/health")
        assert resp.status_code == 200
    # Chama /metrics e checa se as métricas refletem as requisições anteriores
    metrics = client.get("/metrics")
    assert metrics.status_code == 200
    text = metrics.text
    assert "http_requests_total" in text
    assert 'method="GET",path="/health",service_name="integration-test"' in text
    # Checa se a contagem foi incrementada 2x
    import re
    match = re.search(r'http_requests_total{[^}]*path="/health"[^}]*} (\d+)', text)
    assert match
    count = int(match.group(1))
    assert count >= 2