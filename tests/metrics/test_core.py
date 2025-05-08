from prometheus_client import Counter, Gauge, Histogram
import pytest
import solview.metrics.core as core

def test_metric_info_type():
    assert isinstance(core.METRIC_INFO, Gauge)

def test_metric_requests_type_and_increment():
    assert isinstance(core.METRIC_REQUESTS, Counter)
    metric = core.METRIC_REQUESTS.labels(method="GET", path="/", service_name="solview-test")
    before = metric._value.get()
    metric.inc()
    after = metric._value.get()
    assert after == before + 1

def test_metric_responses_labels_and_increment():
    assert isinstance(core.METRIC_RESPONSES, Counter)
    metric = core.METRIC_RESPONSES.labels(method="GET", path="/", status_code="200", service_name="solview-test")
    metric.inc()
    assert metric._value.get() > 0

def test_metric_processing_time_observe():
    assert isinstance(core.METRIC_REQUESTS_PROCESSING_TIME, Histogram)
    metric = core.METRIC_REQUESTS_PROCESSING_TIME.labels(method="GET", path="/", service_name="solview-test")
    metric.observe(0.123)

def test_metric_exceptions_inc():
    assert isinstance(core.METRIC_EXCEPTIONS, Counter)
    metric = core.METRIC_EXCEPTIONS.labels(
        method="GET", path="/", exception_type="ValueError", service_name="solview-test"
    )
    metric.inc()
    assert metric._value.get() > 0

def test_metric_requests_in_progress_inc_dec():
    assert isinstance(core.METRIC_REQUESTS_IN_PROGRESS, Gauge)
    metric = core.METRIC_REQUESTS_IN_PROGRESS.labels(
        method="GET", path="/", service_name="solview-test"
    )
    metric.inc()
    metric.dec()
    # Não deve lançar
