"""FastMCP observability middleware combining OpenTelemetry tracing and Prometheus metrics."""

import random
import time
from typing import Any

from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode

from fastmcp.server.middleware import Middleware, MiddlewareContext, CallNext

from solview.config import get_settings
from solview.instrumentation.utils import MemoryProfiler
from solview.metrics.custom import (
    BUSINESS_OPERATIONS_MEMORY_SAMPLES_TOTAL,
    BUSINESS_OPERATIONS_TOTAL,
    BUSINESS_OPERATIONS_DURATION_SECONDS,
    BUSINESS_OPERATIONS_MEMORY_BYTES,
)
from solview.solview_logging import get_logger

logger = get_logger(__name__)


def _record_memory_metrics(
    profile_memory: bool,
    memory_profiler: MemoryProfiler,
    recording: bool,
    span: trace.Span,
    status: str,
    operation: str,
    app_name: str,
) -> None:
    if not profile_memory:
        return

    BUSINESS_OPERATIONS_MEMORY_SAMPLES_TOTAL.labels(
        operation=operation,
        app_name=app_name,
    ).inc()

    delta = memory_profiler.get_memory_delta()

    if delta is None:
        if recording:
            span.set_attribute("memory.sampled", True)
            span.set_attribute("memory.delta_available", False)
        return

    if delta <= 0:
        if recording:
            span.set_attribute("memory.sampled", True)
            span.set_attribute("memory.delta_bytes", delta)
            span.set_attribute("memory.delta_ignored", True)
        return

    BUSINESS_OPERATIONS_MEMORY_BYTES.labels(
        operation=operation,
        app_name=app_name,
        status=status,
    ).observe(delta)

    if recording:
        span.set_attribute("memory.delta_bytes", delta)
        span.set_attribute("memory.sampled", True)
        span.set_attribute("memory.delta_ignored", False)
        span.set_attribute("memory.delta_available", True)


class SolviewMCPMiddleware(Middleware):
    """
    FastMCP middleware providing observability for MCP server operations.

    Instruments tool calls, resource reads, and prompt retrievals with:
    - OpenTelemetry distributed tracing (spans with MCP-specific attributes)
    - Prometheus metrics (reuses business_operations_* metric family)
    - Optional memory profiling (controlled via SolviewSettings)

    Tool calls are treated as business operations so that dashboards and
    alerts built on ``business_operations_total`` / ``business_operations_duration_seconds``
    work out-of-the-box.

    Usage::

        from fastmcp import FastMCP
        from solview.mcp import SolviewMCPMiddleware

        mcp = FastMCP("MyServer")
        mcp.add_middleware(SolviewMCPMiddleware())
    """

    async def _instrument(
        self,
        operation_type: str,
        operation_name: str,
        context: MiddlewareContext,
        call_next: CallNext,
        span_attributes: dict[str, Any] | None = None,
    ) -> Any:
        operation = f"{operation_type}.{operation_name}"
        tracer = trace.get_tracer(f"mcp.{operation_type}")
        start_time = time.perf_counter()
        success = False

        settings = get_settings()
        app_name = settings.service_name
        profile_memory = (
            settings.enable_memory_profiling
            and random.random() < settings.sampling_memory_profiling
        )
        memory_profiler = MemoryProfiler(enabled=profile_memory)

        with tracer.start_as_current_span(
            f"mcp.{operation}",
            attributes=span_attributes or {},
            record_exception=False,
            set_status_on_exception=False,
        ) as span:
            recording = span.is_recording()

            if recording:
                span.set_attribute("mcp.operation_type", operation_type)
                span.set_attribute("mcp.operation_name", operation_name)
                span.set_attribute("memory.sampling.enabled", profile_memory)

            try:
                with memory_profiler.measure():
                    result = await call_next(context)

                success = True
                span.set_status(Status(StatusCode.OK))
                return result

            except Exception as exc:
                span.record_exception(exc)
                span.set_status(Status(StatusCode.ERROR, description=str(exc)))
                raise

            finally:
                duration = time.perf_counter() - start_time
                status = "success" if success else "error"

                BUSINESS_OPERATIONS_TOTAL.labels(
                    operation=operation,
                    app_name=app_name,
                    status=status,
                ).inc()

                BUSINESS_OPERATIONS_DURATION_SECONDS.labels(
                    operation=operation,
                    app_name=app_name,
                    status=status,
                ).observe(duration)

                _record_memory_metrics(
                    profile_memory=profile_memory,
                    memory_profiler=memory_profiler,
                    recording=recording,
                    span=span,
                    status=status,
                    operation=operation,
                    app_name=app_name,
                )

    async def on_call_tool(self, context, call_next):
        tool_name = context.message.name
        return await self._instrument(
            operation_type="tool",
            operation_name=tool_name,
            context=context,
            call_next=call_next,
            span_attributes={"mcp.tool.name": tool_name},
        )

    async def on_read_resource(self, context, call_next):
        resource_uri = str(context.message.uri)
        return await self._instrument(
            operation_type="resource",
            operation_name=resource_uri,
            context=context,
            call_next=call_next,
            span_attributes={"mcp.resource.uri": resource_uri},
        )

    async def on_get_prompt(self, context, call_next):
        prompt_name = context.message.name
        return await self._instrument(
            operation_type="prompt",
            operation_name=prompt_name,
            context=context,
            call_next=call_next,
            span_attributes={"mcp.prompt.name": prompt_name},
        )
