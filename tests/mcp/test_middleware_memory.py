"""Tests for SolviewMCPMiddleware memory profiling integration."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from fastmcp.server.middleware import MiddlewareContext

from solview.mcp.middleware import SolviewMCPMiddleware
from solview.metrics.custom import (
    BUSINESS_OPERATIONS_MEMORY_SAMPLES_TOTAL,
    BUSINESS_OPERATIONS_MEMORY_BYTES,
)


def _make_tool_context(name="mem_tool"):
    msg = MagicMock()
    msg.name = name
    return MiddlewareContext(message=msg, method="tools/call")


class TestMemoryProfiling:
    @pytest.mark.asyncio
    async def test_memory_samples_counter_incremented(self, mcp_settings_with_memory):
        middleware = SolviewMCPMiddleware()
        context = _make_tool_context("mem_sample_tool")
        call_next = AsyncMock(return_value="ok")

        metric = BUSINESS_OPERATIONS_MEMORY_SAMPLES_TOTAL.labels(
            operation="tool.mem_sample_tool", app_name="test-mcp-app"
        )
        before = metric._value.get()

        await middleware.on_call_tool(context, call_next)

        assert metric._value.get() == before + 1

    @pytest.mark.asyncio
    async def test_no_memory_sampling_when_disabled(self):
        middleware = SolviewMCPMiddleware()
        context = _make_tool_context("no_mem_tool")
        call_next = AsyncMock(return_value="ok")

        metric = BUSINESS_OPERATIONS_MEMORY_SAMPLES_TOTAL.labels(
            operation="tool.no_mem_tool", app_name="test-mcp-app"
        )
        before = metric._value.get()

        await middleware.on_call_tool(context, call_next)

        assert metric._value.get() == before


class TestMemoryDisabled:
    @pytest.mark.asyncio
    async def test_metrics_still_recorded_without_memory(self):
        """Ensures core metrics work when memory profiling is off."""
        from solview.metrics.custom import BUSINESS_OPERATIONS_TOTAL

        middleware = SolviewMCPMiddleware()
        context = _make_tool_context("core_only_tool")
        call_next = AsyncMock(return_value="result")

        metric = BUSINESS_OPERATIONS_TOTAL.labels(
            operation="tool.core_only_tool", app_name="test-mcp-app", status="success"
        )
        before = metric._value.get()

        await middleware.on_call_tool(context, call_next)

        assert metric._value.get() == before + 1
