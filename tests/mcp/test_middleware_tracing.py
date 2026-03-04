"""Tests for SolviewMCPMiddleware OpenTelemetry span creation and attributes."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from fastmcp.server.middleware import MiddlewareContext

from solview.mcp.middleware import SolviewMCPMiddleware


@pytest.fixture(autouse=True)
def otel_exporter():
    trace._TRACER_PROVIDER_SET_ONCE._done = False
    trace._TRACER_PROVIDER = None

    exporter = InMemorySpanExporter()
    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    trace.set_tracer_provider(provider)
    yield exporter
    exporter.clear()
    provider.shutdown()


def _make_context(message, method="tools/call"):
    return MiddlewareContext(message=message, method=method)


class TestToolCallSpan:
    @pytest.mark.asyncio
    async def test_span_created_with_tool_name(self, otel_exporter):
        middleware = SolviewMCPMiddleware()
        msg = MagicMock()
        msg.name = "span_tool"
        context = _make_context(msg, method="tools/call")
        call_next = AsyncMock(return_value="ok")

        await middleware.on_call_tool(context, call_next)

        spans = otel_exporter.get_finished_spans()
        tool_spans = [s for s in spans if "span_tool" in s.name]
        assert len(tool_spans) == 1

        span = tool_spans[0]
        assert span.name == "mcp.tool.span_tool"
        attrs = dict(span.attributes)
        assert attrs["mcp.tool.name"] == "span_tool"
        assert attrs["mcp.operation_type"] == "tool"
        assert attrs["mcp.operation_name"] == "span_tool"

    @pytest.mark.asyncio
    async def test_span_status_ok_on_success(self, otel_exporter):
        middleware = SolviewMCPMiddleware()
        msg = MagicMock()
        msg.name = "ok_tool"
        context = _make_context(msg, method="tools/call")
        call_next = AsyncMock(return_value="result")

        await middleware.on_call_tool(context, call_next)

        spans = otel_exporter.get_finished_spans()
        tool_spans = [s for s in spans if "ok_tool" in s.name]
        assert tool_spans[0].status.status_code == trace.StatusCode.OK

    @pytest.mark.asyncio
    async def test_span_status_error_on_exception(self, otel_exporter):
        middleware = SolviewMCPMiddleware()
        msg = MagicMock()
        msg.name = "err_tool"
        context = _make_context(msg, method="tools/call")
        call_next = AsyncMock(side_effect=RuntimeError("fail"))

        with pytest.raises(RuntimeError):
            await middleware.on_call_tool(context, call_next)

        spans = otel_exporter.get_finished_spans()
        tool_spans = [s for s in spans if "err_tool" in s.name]
        assert tool_spans[0].status.status_code == trace.StatusCode.ERROR

    @pytest.mark.asyncio
    async def test_span_records_exception_event(self, otel_exporter):
        middleware = SolviewMCPMiddleware()
        msg = MagicMock()
        msg.name = "exc_tool"
        context = _make_context(msg, method="tools/call")
        call_next = AsyncMock(side_effect=ValueError("invalid"))

        with pytest.raises(ValueError):
            await middleware.on_call_tool(context, call_next)

        spans = otel_exporter.get_finished_spans()
        tool_spans = [s for s in spans if "exc_tool" in s.name]
        events = tool_spans[0].events
        exception_events = [e for e in events if e.name == "exception"]
        assert len(exception_events) == 1


class TestResourceReadSpan:
    @pytest.mark.asyncio
    async def test_span_created_with_resource_uri(self, otel_exporter):
        middleware = SolviewMCPMiddleware()
        msg = MagicMock()
        msg.uri = "file:///test.csv"
        context = _make_context(msg, method="resources/read")
        call_next = AsyncMock(return_value="csv_data")

        await middleware.on_read_resource(context, call_next)

        spans = otel_exporter.get_finished_spans()
        res_spans = [s for s in spans if "test.csv" in s.name]
        assert len(res_spans) == 1
        assert dict(res_spans[0].attributes)["mcp.resource.uri"] == "file:///test.csv"


class TestPromptGetSpan:
    @pytest.mark.asyncio
    async def test_span_created_with_prompt_name(self, otel_exporter):
        middleware = SolviewMCPMiddleware()
        msg = MagicMock()
        msg.name = "my_prompt"
        context = _make_context(msg, method="prompts/get")
        call_next = AsyncMock(return_value="prompt_result")

        await middleware.on_get_prompt(context, call_next)

        spans = otel_exporter.get_finished_spans()
        prompt_spans = [s for s in spans if "my_prompt" in s.name]
        assert len(prompt_spans) == 1
        assert dict(prompt_spans[0].attributes)["mcp.prompt.name"] == "my_prompt"
