import pytest
from fastapi import FastAPI
from fastapi.responses import PlainTextResponse
from starlette.testclient import TestClient

from solview.metrics.exporters import SolviewPrometheusMiddleware, prometheus_metrics_response
from solview.metrics.core import METRIC_REQUESTS_PROCESSING_TIME

from unittest.mock import patch, MagicMock

@pytest.fixture
def app():
    app = FastAPI()
    app.add_middleware(SolviewPrometheusMiddleware, service_name="trace-test")
    @app.get("/trace")
    def trace():
        return PlainTextResponse("traced")
    app.add_route("/metrics", prometheus_metrics_response)
    return app

def test_middleware_trace_id_exemplar(app):
    # Mock da cadeia do OpenTelemetry: get_current_span().get_span_context().trace_id
    fake_trace_id = 123456789
    fake_formatted_id = "00000000075bcd15"

    mock_ctx = MagicMock()
    mock_ctx.trace_id = fake_trace_id

    mock_span = MagicMock()
    mock_span.get_span_context.return_value = mock_ctx

    with patch("solview.metrics.exporters.trace") as mock_trace:
        mock_trace.get_current_span.return_value = mock_span
        mock_trace.format_trace_id.return_value = fake_formatted_id

        client = TestClient(app)
        resp = client.get("/trace")
        assert resp.status_code == 200

        # A métrica foi observada com exemplares (testa interação, não Prometheus em si)
        # Prometheus_client não armazena o exemplar em Python puro para verificação direta,
        # mas esse teste garante que exemplar foi passado para observe()
        # Você pode verificar chamadas do observe:
        metric = METRIC_REQUESTS_PROCESSING_TIME.labels(method="GET", path="/trace", service_name="trace-test")
        # Observe se o método observe foi chamado com exemplar
        assert metric is not None
        # Para garantir que o método observe foi chamado com kwargs, patch observe!
        with patch.object(metric, "observe", wraps=metric.observe) as mock_observe:
            client.get("/trace")
            # Espera chamada com exemplar
            found_exemplar = False
            for call in mock_observe.call_args_list:
                args, kwargs = call
                if "exemplar" in kwargs and kwargs["exemplar"]["TraceID"] == fake_formatted_id:
                    found_exemplar = True
                    break
            assert found_exemplar, "O exemplar com TraceID foi passado ao observe"