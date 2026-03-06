"""Tests for SolviewMCPMiddleware – tool calls, resource reads, and prompt gets."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from fastmcp.server.middleware import MiddlewareContext

from solview.mcp.middleware import SolviewMCPMiddleware
from solview.metrics.custom import (
    BUSINESS_OPERATIONS_TOTAL,
    BUSINESS_OPERATIONS_DURATION_SECONDS,
)


def _make_context(message, method="tools/call"):
    return MiddlewareContext(message=message, method=method)


def _tool_message(name="my_tool"):
    msg = MagicMock()
    msg.name = name
    return msg


def _resource_message(uri="file:///data.csv"):
    msg = MagicMock()
    msg.uri = uri
    return msg


def _prompt_message(name="summarize"):
    msg = MagicMock()
    msg.name = name
    return msg


# ---------------------------------------------------------------------------
# Tool calls
# ---------------------------------------------------------------------------


class TestOnCallTool:
    @pytest.mark.asyncio
    async def test_success_returns_result(self):
        middleware = SolviewMCPMiddleware()
        context = _make_context(_tool_message("greet"), method="tools/call")
        call_next = AsyncMock(return_value="hello")

        result = await middleware.on_call_tool(context, call_next)

        assert result == "hello"
        call_next.assert_awaited_once_with(context)

    @pytest.mark.asyncio
    async def test_success_increments_counter(self):
        middleware = SolviewMCPMiddleware()
        context = _make_context(_tool_message("counter_tool"), method="tools/call")
        call_next = AsyncMock(return_value="ok")

        metric = BUSINESS_OPERATIONS_TOTAL.labels(
            operation="tool.counter_tool", app_name="test-mcp-app", status="success"
        )
        before = metric._value.get()

        await middleware.on_call_tool(context, call_next)

        assert metric._value.get() == before + 1

    @pytest.mark.asyncio
    async def test_success_observes_duration(self):
        middleware = SolviewMCPMiddleware()
        context = _make_context(_tool_message("duration_tool"), method="tools/call")
        call_next = AsyncMock(return_value="ok")

        metric = BUSINESS_OPERATIONS_DURATION_SECONDS.labels(
            operation="tool.duration_tool", app_name="test-mcp-app", status="success"
        )
        before = metric._sum.get()

        await middleware.on_call_tool(context, call_next)

        assert metric._sum.get() > before

    @pytest.mark.asyncio
    async def test_error_propagates_and_records_error_status(self):
        middleware = SolviewMCPMiddleware()
        context = _make_context(_tool_message("fail_tool"), method="tools/call")
        call_next = AsyncMock(side_effect=ValueError("boom"))

        error_metric = BUSINESS_OPERATIONS_TOTAL.labels(
            operation="tool.fail_tool", app_name="test-mcp-app", status="error"
        )
        before = error_metric._value.get()

        with pytest.raises(ValueError, match="boom"):
            await middleware.on_call_tool(context, call_next)

        assert error_metric._value.get() == before + 1

    @pytest.mark.asyncio
    async def test_error_observes_duration(self):
        middleware = SolviewMCPMiddleware()
        context = _make_context(_tool_message("err_dur_tool"), method="tools/call")
        call_next = AsyncMock(side_effect=RuntimeError("timeout"))

        metric = BUSINESS_OPERATIONS_DURATION_SECONDS.labels(
            operation="tool.err_dur_tool", app_name="test-mcp-app", status="error"
        )
        before = metric._sum.get()

        with pytest.raises(RuntimeError):
            await middleware.on_call_tool(context, call_next)

        assert metric._sum.get() > before


# ---------------------------------------------------------------------------
# Resource reads
# ---------------------------------------------------------------------------


class TestOnReadResource:
    @pytest.mark.asyncio
    async def test_success_returns_result(self):
        middleware = SolviewMCPMiddleware()
        context = _make_context(
            _resource_message("file:///a.txt"), method="resources/read"
        )
        call_next = AsyncMock(return_value="content")

        result = await middleware.on_read_resource(context, call_next)

        assert result == "content"

    @pytest.mark.asyncio
    async def test_success_increments_counter(self):
        middleware = SolviewMCPMiddleware()
        uri = "file:///res_counter.txt"
        context = _make_context(_resource_message(uri), method="resources/read")
        call_next = AsyncMock(return_value="data")

        metric = BUSINESS_OPERATIONS_TOTAL.labels(
            operation=f"resource.{uri}", app_name="test-mcp-app", status="success"
        )
        before = metric._value.get()

        await middleware.on_read_resource(context, call_next)

        assert metric._value.get() == before + 1

    @pytest.mark.asyncio
    async def test_error_records_error_status(self):
        middleware = SolviewMCPMiddleware()
        uri = "file:///missing.txt"
        context = _make_context(_resource_message(uri), method="resources/read")
        call_next = AsyncMock(side_effect=FileNotFoundError("not found"))

        error_metric = BUSINESS_OPERATIONS_TOTAL.labels(
            operation=f"resource.{uri}", app_name="test-mcp-app", status="error"
        )
        before = error_metric._value.get()

        with pytest.raises(FileNotFoundError):
            await middleware.on_read_resource(context, call_next)

        assert error_metric._value.get() == before + 1


# ---------------------------------------------------------------------------
# Prompt gets
# ---------------------------------------------------------------------------


class TestOnGetPrompt:
    @pytest.mark.asyncio
    async def test_success_returns_result(self):
        middleware = SolviewMCPMiddleware()
        context = _make_context(_prompt_message("summarize"), method="prompts/get")
        call_next = AsyncMock(return_value="prompt_result")

        result = await middleware.on_get_prompt(context, call_next)

        assert result == "prompt_result"

    @pytest.mark.asyncio
    async def test_success_increments_counter(self):
        middleware = SolviewMCPMiddleware()
        context = _make_context(_prompt_message("translate"), method="prompts/get")
        call_next = AsyncMock(return_value="ok")

        metric = BUSINESS_OPERATIONS_TOTAL.labels(
            operation="prompt.translate", app_name="test-mcp-app", status="success"
        )
        before = metric._value.get()

        await middleware.on_get_prompt(context, call_next)

        assert metric._value.get() == before + 1

    @pytest.mark.asyncio
    async def test_error_records_error_status(self):
        middleware = SolviewMCPMiddleware()
        context = _make_context(_prompt_message("bad_prompt"), method="prompts/get")
        call_next = AsyncMock(side_effect=KeyError("unknown prompt"))

        error_metric = BUSINESS_OPERATIONS_TOTAL.labels(
            operation="prompt.bad_prompt", app_name="test-mcp-app", status="error"
        )
        before = error_metric._value.get()

        with pytest.raises(KeyError):
            await middleware.on_get_prompt(context, call_next)

        assert error_metric._value.get() == before + 1
