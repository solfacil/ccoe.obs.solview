"""Redis client instrumentation decorators combining OpenTelemetry tracing and Prometheus metrics."""

import random
import time
from collections.abc import Callable
from functools import wraps

from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode

from solview.config import get_settings
from solview.instrumentation.utils import MemoryProfiler
from solview.metrics.custom import (
    REDIS_OPERATIONS_MEMORY_SAMPLES_TOTAL,
    REDIS_OPERATIONS_TOTAL,
    REDIS_OPERATIONS_DURATION_SECONDS,
    REDIS_OPERATIONS_ERRORS_TOTAL,
    REDIS_OPERATIONS_MEMORY_BYTES,
)
from solview.solview_logging import get_logger

logger = get_logger(__name__)


def redis_client_instrumentation(command: str = "command"):
    """
    Decorator to instrument Redis operations with tracing and metrics.

    Usage::

        @redis_client_instrumentation(command="get")
        async def get_cache(key: str) -> str | None:
            return await redis.get(key)

        @redis_client_instrumentation(command="set")
        async def set_cache(key: str, value: str, ttl: int = 300):
            await redis.set(key, value, ex=ttl)
    """

    def decorator(func: Callable) -> Callable:
        def generate_delta_metrics(
            profile_memory,
            memory_profiler,
            recording,
            span,
            status,
            cmd,
            app_name,
        ):
            if not profile_memory:
                return

            REDIS_OPERATIONS_MEMORY_SAMPLES_TOTAL.labels(
                command=cmd,
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

            REDIS_OPERATIONS_MEMORY_BYTES.labels(
                command=cmd,
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
            tracer = trace.get_tracer(f"redis.client.{func.__module__}")
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
                f"redis.{command}",
                attributes={
                    "db.system": "redis",
                    "db.operation": command,
                },
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
                    REDIS_OPERATIONS_ERRORS_TOTAL.labels(
                        command=command,
                        error_type=type(exc).__name__,
                        app_name=app_name,
                    ).inc()

                    span.record_exception(exc)
                    span.set_status(
                        Status(StatusCode.ERROR, description=str(exc))
                    )
                    raise

                finally:
                    duration = time.perf_counter() - start_time
                    status = "success" if success else "error"

                    REDIS_OPERATIONS_TOTAL.labels(
                        command=command,
                        app_name=app_name,
                        status=status,
                    ).inc()

                    REDIS_OPERATIONS_DURATION_SECONDS.labels(
                        command=command,
                        app_name=app_name,
                        status=status,
                    ).observe(duration)

                    generate_delta_metrics(
                        profile_memory=profile_memory,
                        memory_profiler=memory_profiler,
                        recording=recording,
                        span=span,
                        status=status,
                        cmd=command,
                        app_name=app_name,
                    )
        return wrapper
    return decorator
