import pytest
from solview.tracing.core import _get_otlp_span_exporter

def test_otlp_exporter_invalid_protocol():
    with pytest.raises(ValueError):
        _get_otlp_span_exporter(protocol="invalid", host="localhost", port=4317)