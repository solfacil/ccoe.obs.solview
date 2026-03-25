"""RabbitMQ instrumentation decorators combining OpenTelemetry tracing and Prometheus metrics."""

import inspect
import time
import random
from collections.abc import Callable
from functools import wraps

from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode

from solview.config import get_settings
from solview.instrumentation.utils import (
    _get_base_rabbitmq_attributes,
    MemoryProfiler,
)
from solview.metrics.custom import (
    RABBITMQ_MESSAGES_PUBLISHED_TOTAL,
    RABBITMQ_PUBLISHER_DURATION_SECONDS,
    RABBITMQ_PUBLISHER_ERRORS_TOTAL,
    RABBITMQ_PUBLISHER_MEMORY_BYTES,
    RABBITMQ_PUBLISHER_MEMORY_SAMPLES_TOTAL,
    RABBITMQ_MESSAGES_CONSUMED_TOTAL,
    RABBITMQ_CONSUMER_PROCESSING_DURATION_SECONDS,
    RABBITMQ_CONSUMER_ERRORS_TOTAL,
    RABBITMQ_CONSUMER_MEMORY_BYTES,
    RABBITMQ_CONSUMER_MEMORY_SAMPLES_TOTAL,
    RABBITMQ_CONSUMER_LAST_SUCCESS_TIMESTAMP,
    RABBITMQ_CONSUMER_CONSECUTIVE_ERRORS,
)
from solview.solview_logging import get_logger

logger = get_logger(__name__)


def rabbitmq_publisher_instrumentation(operation: str = "publish"):
    """
    Decorator to instrument RabbitMQ publisher operations with tracing and metrics.

    Usage::

        @rabbitmq_publisher_instrumentation(operation="publish")
        async def publish_message(exchange: str, routing_key: str, body: bytes):
            await channel.default_exchange.publish(
                aio_pika.Message(body=body),
                routing_key=routing_key,
            )
    """

    def decorator(func: Callable) -> Callable:
        def generate_delta_metrics(
            profile_memory,
            memory_profiler,
            recording,
            span,
            status,
            routing_key,
            exchange,
            app_name,
        ):
            if not profile_memory:
                return

            RABBITMQ_PUBLISHER_MEMORY_SAMPLES_TOTAL.labels(
                routing_key=routing_key,
                exchange=exchange,
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

            RABBITMQ_PUBLISHER_MEMORY_BYTES.labels(
                routing_key=routing_key,
                exchange=exchange,
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
            sig = inspect.signature(func)
            bound = sig.bind(*args, **kwargs)
            bound.apply_defaults()

            routing_key = bound.arguments.get("routing_key", "")
            exchange = bound.arguments.get("exchange", "")

            tracer = trace.get_tracer(f"rabbitmq.publisher.{func.__module__}")
            start_time = time.perf_counter()
            success = False
            result = None

            settings = get_settings()
            app_name = settings.service_name
            profile_memory = (
                settings.enable_memory_profiling
                and random.random() < settings.sampling_memory_profiling
            )
            memory_profiler = MemoryProfiler(enabled=profile_memory)

            with tracer.start_as_current_span(
                f"rabbitmq.publisher.{operation}",
                attributes={
                    "messaging.system": "rabbitmq",
                    "messaging.destination": exchange or routing_key,
                    "messaging.operation": operation,
                    "messaging.rabbitmq.routing_key": routing_key,
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
                    RABBITMQ_PUBLISHER_ERRORS_TOTAL.labels(
                        routing_key=routing_key,
                        exchange=exchange,
                        error_type=type(exc).__name__,
                        app_name=app_name,
                    ).inc()

                    span.record_exception(exc)
                    span.set_status(Status(StatusCode.ERROR, description=str(exc)))
                    raise

                finally:
                    duration = time.perf_counter() - start_time
                    status = "success" if success else "error"

                    if success:
                        RABBITMQ_MESSAGES_PUBLISHED_TOTAL.labels(
                            routing_key=routing_key,
                            exchange=exchange,
                            app_name=app_name,
                        ).inc()

                    RABBITMQ_PUBLISHER_DURATION_SECONDS.labels(
                        routing_key=routing_key,
                        exchange=exchange,
                        app_name=app_name,
                        status=status,
                    ).observe(duration)

                    generate_delta_metrics(
                        profile_memory=profile_memory,
                        memory_profiler=memory_profiler,
                        recording=recording,
                        span=span,
                        status=status,
                        routing_key=routing_key,
                        exchange=exchange,
                        app_name=app_name,
                    )

        return wrapper

    return decorator


def rabbitmq_consumer_instrumentation(operation: str = "process"):
    """
    Decorator to instrument RabbitMQ consumer operations with tracing and metrics.

    Usage::

        @rabbitmq_consumer_instrumentation(operation="process")
        async def process_message(queue: str, message: aio_pika.IncomingMessage):
            async with message.process():
                data = json.loads(message.body)
                await handle(data)
    """

    def decorator(func: Callable) -> Callable:
        def generate_delta_metrics_consumer(
            profile_memory,
            memory_profiler,
            recording,
            span,
            status,
            queue,
            handler,
            app_name,
        ):
            if not profile_memory:
                return

            RABBITMQ_CONSUMER_MEMORY_SAMPLES_TOTAL.labels(
                queue=queue,
                handler=handler,
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

            RABBITMQ_CONSUMER_MEMORY_BYTES.labels(
                queue=queue,
                handler=operation,
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
            sig = inspect.signature(func)
            bound = sig.bind(*args, **kwargs)
            bound.apply_defaults()

            queue = bound.arguments.get("queue")

            tracer = trace.get_tracer(f"rabbitmq.consumer.{func.__module__}")
            start_time = time.perf_counter()
            success = False
            result = None

            settings = get_settings()
            app_name = settings.service_name
            profile_memory = (
                settings.enable_memory_profiling
                and random.random() < settings.sampling_memory_profiling
            )
            memory_profiler = MemoryProfiler(enabled=profile_memory)

            with tracer.start_as_current_span(
                f"rabbitmq.consumer.{operation}",
                attributes=_get_base_rabbitmq_attributes(
                    destination=queue,
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
                    return result

                except Exception as exc:
                    RABBITMQ_CONSUMER_ERRORS_TOTAL.labels(
                        queue=queue,
                        error_type=type(exc).__name__,
                        app_name=app_name,
                    ).inc()

                    span.record_exception(exc)
                    span.set_status(Status(StatusCode.ERROR, description=str(exc)))
                    raise

                finally:
                    duration = time.perf_counter() - start_time
                    status = "success" if success else "error"

                    if success:
                        if operation == "receive":
                            RABBITMQ_MESSAGES_CONSUMED_TOTAL.labels(
                                queue=queue,
                                app_name=app_name,
                            ).inc()

                        RABBITMQ_CONSUMER_LAST_SUCCESS_TIMESTAMP.labels(
                            queue=queue,
                            app_name=app_name,
                        ).set_to_current_time()

                        RABBITMQ_CONSUMER_CONSECUTIVE_ERRORS.labels(
                            queue=queue,
                            app_name=app_name,
                        ).set(0)
                    else:
                        RABBITMQ_CONSUMER_CONSECUTIVE_ERRORS.labels(
                            queue=queue,
                            app_name=app_name,
                        ).inc()

                    RABBITMQ_CONSUMER_PROCESSING_DURATION_SECONDS.labels(
                        queue=queue,
                        handler=operation,
                        app_name=app_name,
                        status=status,
                    ).observe(duration)

                    generate_delta_metrics_consumer(
                        profile_memory=profile_memory,
                        memory_profiler=memory_profiler,
                        recording=recording,
                        span=span,
                        status=status,
                        queue=queue,
                        handler=operation,
                        app_name=app_name,
                    )

        return wrapper

    return decorator
