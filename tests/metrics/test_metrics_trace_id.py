import pytest
from fastapi import FastAPI
from starlette.testclient import TestClient
from unittest.mock import patch, MagicMock

def test_trace_id_exemplar_in_histogram(app):
    from unittest.mock import patch, MagicMock
    fake_trace_id = 42
    fake_formatted = "000000000000002a"
    mock_ctx = MagicMock(trace_id=fake_trace_id)
    mock_span = MagicMock()
    mock_span.get_span_context.return_value = mock_ctx
    with patch("solview.metrics.exporters.trace") as mock_trace:
        mock_trace.get_current_span.return_value = mock_span
        mock_trace.format_trace_id.return_value = fake_formatted
        client = TestClient(app)
        from solview.metrics.core import METRIC_REQUESTS_PROCESSING_TIME
        metric = METRIC_REQUESTS_PROCESSING_TIME.labels(method="GET", path="/ping", service_name="test-app")
        with patch.object(metric, "observe", wraps=metric.observe) as mock_observe:
            client.get("/ping")
            has_exemplar = False
            for call in mock_observe.call_args_list:
                args, kwargs = call
                # print("KWARGS:", kwargs)
                if "exemplar" in kwargs and kwargs["exemplar"].get("TraceID") == fake_formatted:
                    has_exemplar = True
            assert has_exemplar, "O exemplar com TraceID foi passado ao observe"