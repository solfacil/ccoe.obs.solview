"""Kafka instrumentation decorators combining OpenTelemetry tracing and Prometheus metrics."""

import inspect
import time
import random
from collections.abc import Callable
from functools import wraps

from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode

from solview.instrumentation.utils import (
    _extract_topic_from_args,
    _get_base_kafka_attributes,
    MemoryProfiler,
)
from solview.metrics.custom import (
    KAFKA_CONSUMER_MEMORY_SAMPLES_TOTAL,
    KAFKA_MESSAGES_CONSUMED_TOTAL,
    KAFKA_MESSAGES_PRODUCED_TOTAL,
    KAFKA_PRODUCER_DURATION_SECONDS,
    KAFKA_PRODUCER_ERRORS_TOTAL,
    KAFKA_CONSUMER_ERRORS_TOTAL,
    KAFKA_MESSAGE_PROCESSING_DURATION_SECONDS,
    KAFKA_PRODUCER_MEMORY_BYTES,
    KAFKA_CONSUMER_MEMORY_BYTES,
    KAFKA_PRODUCER_MEMORY_SAMPLES_TOTAL,
)
from solview.solview_logging import get_logger
from solview.settings import SolviewSettings

logger = get_logger(__name__)
settings = SolviewSettings()
APP_NAME = settings.service_name


def kafka_producer_instrumentation(operation: str = "send"):
    """
    Decorator to instrument Kafka producer operations with tracing and metrics.
    """

    def decorator(func: Callable) -> Callable:

        def should_profile_memory() -> bool:
            return (
                settings.enable_memory_profiling
                and random.random() < settings.sampling_memory_profiling
            )

        @wraps(func)
        async def wrapper(*args, **kwargs):
            sig = inspect.signature(func)
            bound = sig.bind(*args, **kwargs)
            bound.apply_defaults()

            topic = bound.arguments.get("topic")
            key = bound.arguments.get("key", "") 

            tracer = trace.get_tracer(f"kafka.producer.{func.__module__}")
            start_time = time.perf_counter()
            success = False
            result = None

            profile_memory = should_profile_memory()
            memory_profiler = MemoryProfiler(enabled=profile_memory)

            with tracer.start_as_current_span(
                f"kafka.producer.{operation}",
                attributes={
                    "messaging.system": "kafka",
                    "messaging.destination": topic,
                    "messaging.operation": operation,
                    "messaging.kafka.message_key": key,
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

                except Exception as exc:
                    KAFKA_PRODUCER_ERRORS_TOTAL.labels(
                        topic=topic,
                        error_type=type(exc).__name__,
                        app_name=APP_NAME,
                    ).inc()

                    span.record_exception(exc)
                    span.set_status(
                        Status(StatusCode.ERROR, description=str(exc))
                    )
                    raise

                finally:
                    duration = time.perf_counter() - start_time
                    status = "success" if success else "error"

                    if success:
                        KAFKA_MESSAGES_PRODUCED_TOTAL.labels(
                            topic=topic,
                            app_name=APP_NAME,
                        ).inc()

                    KAFKA_PRODUCER_DURATION_SECONDS.labels(
                        topic=topic,
                        app_name=APP_NAME,
                        status=status,
                    ).observe(duration)

                    if not profile_memory:
                        return result

                    KAFKA_PRODUCER_MEMORY_SAMPLES_TOTAL.labels(
                        topic=topic,
                        app_name=APP_NAME,
                    ).inc()

                    delta = memory_profiler.get_memory_delta()

                    if delta is None:
                        if recording:
                            span.set_attribute("memory.sampled", True)
                            span.set_attribute("memory.delta_available", False)
                        return result

                    if delta <= 0:
                        if recording:
                            span.set_attribute("memory.sampled", True)
                            span.set_attribute("memory.delta_bytes", delta)
                            span.set_attribute("memory.delta_ignored", True)
                        return result

                    KAFKA_PRODUCER_MEMORY_BYTES.labels(
                        topic=topic,
                        app_name=APP_NAME,
                        status=status,
                    ).observe(delta)

                    if recording:
                        span.set_attribute("memory.sampled", True)
                        span.set_attribute("memory.delta_bytes", delta)
                        span.set_attribute("memory.delta_available", True)
                        span.set_attribute("memory.delta_ignored", False)

                return result

        return wrapper

    return decorator

def kafka_consumer_instrumentation(operation: str = "process"):
    """
    Decorator to instrument Kafka consumer operations with tracing and metrics.
    """

    def decorator(func: Callable) -> Callable:

        def should_profile_memory() -> bool:
            return (
                settings.enable_memory_profiling
                and random.random() < settings.sampling_memory_profiling
            )

        @wraps(func)
        async def wrapper(*args, **kwargs):
            sig = inspect.signature(func)
            bound = sig.bind(*args, **kwargs)
            bound.apply_defaults()

            topic = bound.arguments.get("topic")

            tracer = trace.get_tracer(f"kafka.consumer.{func.__module__}")
            start_time = time.perf_counter()
            success = False
            result = None

            profile_memory = should_profile_memory()
            memory_profiler = MemoryProfiler(enabled=profile_memory)

            with tracer.start_as_current_span(
                f"kafka.consumer.{operation}",
                attributes=_get_base_kafka_attributes(
                    topic=topic,
                    operation=operation,
                    system_type="consumer",
                ),
            ) as span:
                recording = span.is_recording()
                if recording:
                    span.set_attribute("memory.sampling.enabled", profile_memory)

                try:
                    with memory_profiler.measure():
                        result = await func(*args, **kwargs)

                    success = True
                    span.set_status(Status(StatusCode.OK))

                except Exception as exc:
                    KAFKA_CONSUMER_ERRORS_TOTAL.labels(
                        topic=topic,
                        error_type=type(exc).__name__,
                        app_name=APP_NAME,
                    ).inc()

                    span.record_exception(exc)
                    span.set_status(
                        Status(StatusCode.ERROR, description=str(exc))
                    )
                    raise

                finally:
                    duration = time.perf_counter() - start_time
                    status = "success" if success else "error"

                    if success and operation == "receive":
                        KAFKA_MESSAGES_CONSUMED_TOTAL.labels(
                            topic=topic,
                            app_name=APP_NAME,
                        ).inc()

                    KAFKA_MESSAGE_PROCESSING_DURATION_SECONDS.labels(
                        topic=topic,
                        handler=operation,
                        app_name=APP_NAME,
                        status=status,
                    ).observe(duration)

                    if not profile_memory:
                        return result

                    KAFKA_CONSUMER_MEMORY_SAMPLES_TOTAL.labels(
                        topic=topic,
                        handler=operation,
                        app_name=APP_NAME,
                    ).inc()

                    delta = memory_profiler.get_memory_delta()

                    if delta is None:
                        if recording:
                            span.set_attribute("memory.sampled", True)
                            span.set_attribute("memory.delta_available", False)
                        return result

                    if delta <= 0:
                        if recording:
                            span.set_attribute("memory.sampled", True)
                            span.set_attribute("memory.delta_bytes", delta)
                            span.set_attribute("memory.delta_ignored", True)
                        return result

                    KAFKA_CONSUMER_MEMORY_BYTES.labels(
                        topic=topic,
                        handler=operation,
                        app_name=APP_NAME,
                        status=status,
                    ).observe(delta)

                    if recording:
                        span.set_attribute("memory.sampled", True)
                        span.set_attribute("memory.delta_bytes", delta)
                        span.set_attribute("memory.delta_available", True)
                        span.set_attribute("memory.delta_ignored", False)

                return result

        return wrapper

    return decorator