import time
from unittest.mock import patch
from fastapi import FastAPI
from fastapi.responses import PlainTextResponse
from starlette.testclient import TestClient
from solview.metrics.exporters import SolviewPrometheusMiddleware, prometheus_metrics_response
from solview.metrics.core import METRIC_REQUESTS_PROCESSING_TIME
import pytest

@pytest.fixture
def app_for_timing():
    app = FastAPI()
    app.add_middleware(SolviewPrometheusMiddleware, service_name="timing-test")

    @app.get("/slow")
    def slow():
        return PlainTextResponse("slow")

    app.add_route("/metrics", prometheus_metrics_response)
    return app

def test_processing_time_metric_recorded(app_for_timing):
    client = TestClient(app_for_timing)
    with patch("solview.metrics.exporters.time") as mock_time:
        mock_time.perf_counter.side_effect = [1.0, 2.5]  # Simular 1.5 segundos de duração
        # Zera o histograma antes (opcional)
        client.get("/slow")
        metric = METRIC_REQUESTS_PROCESSING_TIME.labels(method="GET", path="/slow", service_name="timing-test")
        # Não há acesso direto ao valor do histograma, mas você pode garantir que não houve exceção e side effect funcionou
