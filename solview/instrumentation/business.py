"""Business operations instrumentation decorators combining OpenTelemetry tracing and Prometheus metrics."""

import asyncio
import inspect
import random
import time
from collections.abc import Callable
from functools import wraps

from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode

from solview.metrics.custom import (
    BUSINESS_OPERATIONS_MEMORY_SAMPLES_TOTAL,
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


def business_operation_instrumentation(operation: str):
    """
    Decorator to instrument business operations with tracing and metrics.
    """

    def decorator(func: Callable) -> Callable:

        def should_profile_memory() -> bool:
            return (
                settings.enable_memory_profiling
                and random.random() < settings.sampling_memory_profiling
            )

        def generate_delta_metrics(
            profile_memory,
            memory_profiler,
            recording,
            span,
            status,
            operation,
            app_name,
        ):
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
                
        @wraps(func)
        async def wrapper(*args, **kwargs):
            tracer = trace.get_tracer(f"business.{func.__module__}")
            start_time = time.perf_counter()
            success = False
            result = None

            profile_memory = should_profile_memory()
            memory_profiler = MemoryProfiler(enabled=profile_memory)

            with tracer.start_as_current_span(
                f"business.{operation}"
            ) as span:
                recording = span.is_recording()

                if recording:
                    span.set_attribute("memory.sampling.enabled", profile_memory)

                try:
                    with memory_profiler.measure():
                        result = await func(*args, **kwargs)

                    success = True
                    span.set_status(Status(StatusCode.OK))
                    return result

                except Exception as exc:
                    span.record_exception(exc)
                    span.set_status(
                        Status(StatusCode.ERROR, description=str(exc))
                    )
                    raise
                    
                finally:
                    duration = time.perf_counter() - start_time
                    status = "success" if success else "error"

                    BUSINESS_OPERATIONS_TOTAL.labels(
                        operation=operation,
                        app_name=APP_NAME,
                        status=status,
                    ).inc()

                    BUSINESS_OPERATIONS_DURATION_SECONDS.labels(
                        operation=operation,
                        app_name=APP_NAME,
                        status=status,
                    ).observe(duration)

                    generate_delta_metrics(
                        profile_memory=profile_memory,
                        memory_profiler=memory_profiler,
                        recording=recording,
                        span=span,
                        status=status,
                        operation=operation,
                        app_name=APP_NAME,
                    )
        return wrapper

    return decorator

