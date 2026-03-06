"""Tests for setup_tracer() without app — the path used by FastMCP servers."""

import os
import pytest
from unittest.mock import patch, MagicMock

from opentelemetry import trace as _trace
from opentelemetry.metrics import _internal as _metrics_internal
from opentelemetry.sdk.trace import TracerProvider

from solview.settings import SolviewSettings
from solview.config import setup_settings
from solview.tracing import setup_tracer


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


class TestSetupTracerWithoutApp:
    """Testa setup_tracer() sem app (cenário FastMCP / scripts)."""

    def test_returns_tracer_provider(self):
        setup_settings(
            SolviewSettings(
                service_name="mcp-tracer-test",
                use_console_exporter_on_unittest=True,
            )
        )
        os.environ["PYTHON_ENV"] = "unittest"

        provider = setup_tracer()

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

        provider = setup_tracer()

        assert _trace.get_tracer_provider() is provider
        os.environ.pop("PYTHON_ENV", None)

    @patch("solview.tracing.core.HTTPXClientInstrumentor")
    @patch("solview.tracing.core.RequestsInstrumentor")
    @patch("solview.tracing.core.AsyncPGInstrumentor")
    @patch("solview.tracing.core.SQLAlchemyInstrumentor")
    @patch("solview.tracing.core.RedisInstrumentor")
    @patch("solview.tracing.core.LoggingInstrumentor")
    @patch("solview.tracing.core.HttpClientInstrumentor")
    @patch("solview.tracing.core._get_otlp_span_exporter")
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

        setup_tracer()

        mock_httpx.return_value.instrument.assert_called_once()
        mock_requests.return_value.instrument.assert_called_once()
        mock_asyncpg.return_value.instrument.assert_called_once()
        mock_sqlalchemy.return_value.instrument.assert_called_once()
        mock_redis.return_value.instrument.assert_called_once()
        mock_logging.return_value.instrument.assert_called_once()
        mock_http_client.return_value.instrument.assert_called_once()

    @patch("solview.tracing.core.HTTPXClientInstrumentor")
    @patch("solview.tracing.core.RequestsInstrumentor")
    @patch("solview.tracing.core.AsyncPGInstrumentor")
    @patch("solview.tracing.core.SQLAlchemyInstrumentor")
    @patch("solview.tracing.core.RedisInstrumentor")
    @patch("solview.tracing.core.LoggingInstrumentor")
    @patch("solview.tracing.core.HttpClientInstrumentor")
    @patch("solview.tracing.core._get_otlp_span_exporter")
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

        setup_tracer()

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

        provider = setup_tracer()

        assert isinstance(provider, TracerProvider)
        processors = getattr(provider, "_active_span_processor", None)
        assert processors is not None
        os.environ.pop("PYTHON_ENV", None)


class TestNoFastAPIDependencyWithoutApp:
    """Garante que setup_tracer() sem app não invoca FastAPIInstrumentor."""

    @patch("solview.tracing.core.HTTPXClientInstrumentor")
    @patch("solview.tracing.core.RequestsInstrumentor")
    @patch("solview.tracing.core.AsyncPGInstrumentor")
    @patch("solview.tracing.core.SQLAlchemyInstrumentor")
    @patch("solview.tracing.core.RedisInstrumentor")
    @patch("solview.tracing.core.LoggingInstrumentor")
    @patch("solview.tracing.core.HttpClientInstrumentor")
    @patch("solview.tracing.core._get_otlp_span_exporter")
    def test_fastapi_instrumentor_not_called_without_app(
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
        """Quando app=None, FastAPIInstrumentor e Instrumentator não são importados."""
        setup_settings(SolviewSettings(service_name="no-fastapi-test"))
        mock_otlp.return_value = MagicMock()

        with patch.dict("sys.modules", {
            "fastapi": MagicMock(),
            "prometheus_fastapi_instrumentator": MagicMock(),
            "opentelemetry.instrumentation.fastapi": MagicMock(),
        }) as patched:
            setup_tracer()

        import sys
        fastapi_mod = sys.modules.get("opentelemetry.instrumentation.fastapi")
        if fastapi_mod and hasattr(fastapi_mod, "FastAPIInstrumentor"):
            fastapi_mod.FastAPIInstrumentor.return_value.instrument_app.assert_not_called()
