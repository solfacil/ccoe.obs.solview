from solview.metrics.core import METRIC_REQUESTS_IN_PROGRESS
from starlette.testclient import TestClient

def test_requests_in_progress_inc_and_dec_called(app):
    client = TestClient(app)
    metric = METRIC_REQUESTS_IN_PROGRESS.labels(method="GET", path="/ping", service_name="test-app")
    before = metric._value.get()
    client.get("/ping")
    after = metric._value.get()
    assert after == before