"""Business operations instrumentation decorators combining OpenTelemetry tracing and Prometheus metrics."""

import asyncio
import random
import time
from collections.abc import Callable
from functools import wraps

from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode

from solview.metrics.custom import (
    BUSINESS_OPERATIONS_TOTAL,
    BUSINESS_OPERATIONS_DURATION_SECONDS,
    BUSINESS_OPERATIONS_MEMORY_BYTES,
)
from solview.instrumentation.utils import MemoryProfiler
from solview.solview_logging import get_logger
from solview.settings import SolviewSettings

logger = get_logger(__name__)
settings = SolviewSettings()
APP_NAME = settings.service_name


def business_operation_instrumentation(operation_name: str):
    """
    Decorator to instrument business operations with tracing and metrics.
    Supports both async and sync functions.
    """

    def decorator(func: Callable) -> Callable:

        def _should_profile_memory() -> bool:
            sampling = random.random() < settings.sampling_memory_profiling
            return (
                settings.enable_memory_profiling
                and sampling
            )

        async def _execute_async(func, *args, **kwargs):
            return await func(*args, **kwargs)

        def _execute_sync(func, *args, **kwargs):
            return func(*args, **kwargs)

        def _wrapper(executor):
            @wraps(func)
            async def wrapped(*args, **kwargs):
                tracer = trace.get_tracer(f"business.{func.__module__}")
                start_time = time.time()
                success = False

                profile_memory = _should_profile_memory()
                memory_profiler = MemoryProfiler(enabled=profile_memory)

                with tracer.start_as_current_span(f"business.{operation_name}") as span:
                    with memory_profiler.measure():
                        try:
                            result = executor(func, *args, **kwargs)
                            if asyncio.iscoroutine(result):
                                result = await result

                            success = True
                            span.set_status(Status(StatusCode.OK))
                            return result

                        except Exception as e:
                            span.set_status(
                                Status(StatusCode.ERROR, description=str(e))
                            )
                            span.record_exception(e)
                            raise

                        finally:
                            duration = time.time() - start_time
                            status = "success" if success else "error"

                            # ⏱ Duration (sempre)
                            BUSINESS_OPERATIONS_DURATION_SECONDS.labels(
                                operation=operation_name,
                                app_name=APP_NAME,
                                status=status,
                            ).observe(duration)

                            # 🔢 Total executions
                            BUSINESS_OPERATIONS_TOTAL.labels(
                                operation=operation_name,
                                app_name=APP_NAME,
                                status=status,
                            ).inc()

                            # 🧠 Memory metrics (somente se amostrado)
                            if profile_memory:
                                memory_delta = memory_profiler.get_memory_delta()
                                if memory_delta is not None:
                                    BUSINESS_OPERATIONS_MEMORY_BYTES.labels(
                                        operation=operation_name,
                                        app_name=APP_NAME,
                                        status=status,
                                    ).observe(abs(memory_delta))

                                    if span.is_recording():
                                        span.set_attribute(
                                            "memory.delta_bytes",
                                            memory_delta,
                                        )

            return wrapped

        if asyncio.iscoroutinefunction(func):
            return _wrapper(_execute_async)
        else:
            return _wrapper(_execute_sync)

    return decorator

