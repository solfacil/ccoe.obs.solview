"""Tests for setup_mcp_tracer – TracerProvider, MeterProvider and library instrumentors."""

import os
import pytest
from unittest.mock import patch, MagicMock

from opentelemetry import trace as _trace
from opentelemetry.metrics import _internal as _metrics_internal
from opentelemetry.sdk.trace import TracerProvider

from solview.settings import SolviewSettings
from solview.config import setup_settings
from solview.mcp.tracing import setup_mcp_tracer


@pytest.fixture(autouse=True)
def _reset_providers():
    """Garante que cada teste parte de um estado limpo de providers."""
    _trace._TRACER_PROVIDER_SET_ONCE._done = False
    _trace._TRACER_PROVIDER = None
    _metrics_internal._METER_PROVIDER_SET_ONCE._done = False
    _metrics_internal._METER_PROVIDER = None

    yield

    try:
        provider = _trace.get_tracer_provider()
        if isinstance(provider, TracerProvider):
            provider.shutdown()
    except Exception:
        pass


class TestSetupMcpTracer:
    def test_returns_tracer_provider(self):
        setup_settings(
            SolviewSettings(
                service_name="mcp-tracer-test",
                use_console_exporter_on_unittest=True,
            )
        )
        os.environ["PYTHON_ENV"] = "unittest"

        provider = setup_mcp_tracer()

        assert isinstance(provider, TracerProvider)
        os.environ.pop("PYTHON_ENV", None)

    def test_tracer_provider_is_set_globally(self):
        setup_settings(
            SolviewSettings(
                service_name="mcp-global-test",
                use_console_exporter_on_unittest=True,
            )
        )
        os.environ["PYTHON_ENV"] = "unittest"

        provider = setup_mcp_tracer()

        assert _trace.get_tracer_provider() is provider
        os.environ.pop("PYTHON_ENV", None)

    @patch("solview.mcp.tracing.HTTPXClientInstrumentor")
    @patch("solview.mcp.tracing.RequestsInstrumentor")
    @patch("solview.mcp.tracing.AsyncPGInstrumentor")
    @patch("solview.mcp.tracing.SQLAlchemyInstrumentor")
    @patch("solview.mcp.tracing.RedisInstrumentor")
    @patch("solview.mcp.tracing.LoggingInstrumentor")
    @patch("solview.mcp.tracing.HttpClientInstrumentor")
    @patch("solview.mcp.tracing._get_otlp_span_exporter")
    def test_all_library_instrumentors_called(
        self,
        mock_otlp,
        mock_http_client,
        mock_logging,
        mock_redis,
        mock_sqlalchemy,
        mock_asyncpg,
        mock_requests,
        mock_httpx,
    ):
        setup_settings(SolviewSettings(service_name="mcp-instr-test"))
        mock_otlp.return_value = MagicMock()

        setup_mcp_tracer()

        mock_httpx.return_value.instrument.assert_called_once()
        mock_requests.return_value.instrument.assert_called_once()
        mock_asyncpg.return_value.instrument.assert_called_once()
        mock_sqlalchemy.return_value.instrument.assert_called_once()
        mock_redis.return_value.instrument.assert_called_once()
        mock_logging.return_value.instrument.assert_called_once()
        mock_http_client.return_value.instrument.assert_called_once()

    @patch("solview.mcp.tracing.HTTPXClientInstrumentor")
    @patch("solview.mcp.tracing.RequestsInstrumentor")
    @patch("solview.mcp.tracing.AsyncPGInstrumentor")
    @patch("solview.mcp.tracing.SQLAlchemyInstrumentor")
    @patch("solview.mcp.tracing.RedisInstrumentor")
    @patch("solview.mcp.tracing.LoggingInstrumentor")
    @patch("solview.mcp.tracing.HttpClientInstrumentor")
    @patch("solview.mcp.tracing._get_otlp_span_exporter")
    def test_sqlalchemy_commenter_setting_forwarded(
        self,
        mock_otlp,
        mock_http_client,
        mock_logging,
        mock_redis,
        mock_sqlalchemy,
        mock_asyncpg,
        mock_requests,
        mock_httpx,
    ):
        setup_settings(
            SolviewSettings(
                service_name="mcp-commenter-test",
                otlp_sqlalchemy_enable_commenter=True,
            )
        )
        mock_otlp.return_value = MagicMock()

        setup_mcp_tracer()

        mock_sqlalchemy.return_value.instrument.assert_called_once_with(
            enable_commenter=True,
            commenter_options={},
        )

    def test_unittest_mode_uses_console_exporter(self):
        setup_settings(
            SolviewSettings(
                service_name="mcp-console-test",
                use_console_exporter_on_unittest=True,
            )
        )
        os.environ["PYTHON_ENV"] = "unittest"

        provider = setup_mcp_tracer()

        assert isinstance(provider, TracerProvider)
        processors = getattr(provider, "_active_span_processor", None)
        assert processors is not None
        os.environ.pop("PYTHON_ENV", None)


class TestNoFastAPIDependency:
    @patch("solview.mcp.tracing.HTTPXClientInstrumentor")
    @patch("solview.mcp.tracing.RequestsInstrumentor")
    @patch("solview.mcp.tracing.AsyncPGInstrumentor")
    @patch("solview.mcp.tracing.SQLAlchemyInstrumentor")
    @patch("solview.mcp.tracing.RedisInstrumentor")
    @patch("solview.mcp.tracing.LoggingInstrumentor")
    @patch("solview.mcp.tracing.HttpClientInstrumentor")
    @patch("solview.mcp.tracing._get_otlp_span_exporter")
    def test_does_not_import_fastapi_instrumentator(
        self,
        mock_otlp,
        mock_http_client,
        mock_logging,
        mock_redis,
        mock_sqlalchemy,
        mock_asyncpg,
        mock_requests,
        mock_httpx,
    ):
        """Garante que setup_mcp_tracer não usa FastAPIInstrumentor nem Instrumentator."""
        import solview.mcp.tracing as _mod

        source = open(_mod.__file__).read()
        assert "FastAPIInstrumentor" not in source
        assert "prometheus_fastapi_instrumentator" not in source
