"""Kafka instrumentation decorators combining OpenTelemetry tracing and Prometheus metrics."""

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
    KAFKA_MESSAGES_CONSUMED_TOTAL,
    KAFKA_MESSAGES_PRODUCED_TOTAL,
    KAFKA_PRODUCER_DURATION_SECONDS,
    KAFKA_PRODUCER_ERRORS_TOTAL,
    KAFKA_CONSUMER_ERRORS_TOTAL,
    KAFKA_MESSAGE_PROCESSING_DURATION_SECONDS,
    KAFKA_PRODUCER_MEMORY_BYTES,
    KAFKA_CONSUMER_MEMORY_BYTES,
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

        def _should_profile_memory() -> bool:
            return (
                settings.enable_memory_profiling
                and random.random() < settings.sampling_memory_profiling
            )

        @wraps(func)
        async def wrapper(*args, **kwargs):
            topic = kwargs.get("topic") or (args[1] if len(args) > 1 else "unknown")
            key = kwargs.get("key") or (args[2] if len(args) > 2 else "unknown")

            tracer = trace.get_tracer(f"kafka.producer.{func.__module__}")
            start_time = time.time()
            success = False

            profile_memory = _should_profile_memory()
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
                with memory_profiler.measure():
                    try:
                        result = await func(*args, **kwargs)
                        success = True
                        span.set_status(Status(StatusCode.OK))
                        return result

                    except Exception as e:
                        KAFKA_PRODUCER_ERRORS_TOTAL.labels(
                            topic=topic,
                            error_type=type(e).__name__,
                            app_name=APP_NAME,
                        ).inc()

                        span.set_status(
                            Status(StatusCode.ERROR, description=str(e))
                        )
                        span.record_exception(e)
                        logger.error(
                            f"Error in kafka producer {operation} for topic {topic}: {e}"
                        )
                        raise

                    finally:
                        duration = time.time() - start_time
                        status = "success" if success else "error"

                        # 🔢 Total produced (only on success)
                        if success:
                            KAFKA_MESSAGES_PRODUCED_TOTAL.labels(
                                topic=topic,
                                app_name=APP_NAME,
                            ).inc()

                        # ⏱ Duration (sempre)
                        KAFKA_PRODUCER_DURATION_SECONDS.labels(
                            topic=topic,
                            app_name=APP_NAME,
                            status=status,
                        ).observe(duration)

                        # 🧠 Memory (amostrado)
                        if profile_memory:
                            memory_delta = memory_profiler.get_memory_delta()
                            if memory_delta is not None:
                                KAFKA_PRODUCER_MEMORY_BYTES.labels(
                                    topic=topic,
                                    app_name=APP_NAME,
                                    status=status,
                                ).observe(abs(memory_delta))

                                if span.is_recording():
                                    span.set_attribute(
                                        "memory.delta_bytes", memory_delta
                                    )

        return wrapper

    return decorator

def kafka_consumer_instrumentation(operation: str = "process"):
    """
    Decorator to instrument Kafka consumer operations with tracing and metrics.
    """

    def decorator(func: Callable) -> Callable:

        def _should_profile_memory() -> bool:
            return (
                settings.enable_memory_profiling
                and random.random() < settings.sampling_memory_profiling
            )

        @wraps(func)
        async def wrapper(*args, **kwargs):
            topic = _extract_topic_from_args(args, kwargs)
            tracer = trace.get_tracer(f"kafka.consumer.{func.__module__}")
            start_time = time.time()
            success = False

            profile_memory = _should_profile_memory()
            memory_profiler = MemoryProfiler(enabled=profile_memory)

            with tracer.start_as_current_span(
                f"kafka.consumer.{operation}",
                attributes=_get_base_kafka_attributes(
                    topic=topic,
                    operation=operation,
                    role="consumer",
                ),
            ) as span:
                with memory_profiler.measure():
                    try:
                        result = await func(*args, **kwargs)
                        success = True
                        span.set_status(Status(StatusCode.OK))
                        return result

                    except Exception as e:
                        KAFKA_CONSUMER_ERRORS_TOTAL.labels(
                            topic=topic,
                            error_type=type(e).__name__,
                            app_name=APP_NAME,
                        ).inc()

                        span.set_status(
                            Status(StatusCode.ERROR, description=str(e))
                        )
                        span.record_exception(e)
                        logger.error(
                            f"Error in kafka consumer {operation} for topic {topic}: {e}"
                        )
                        raise

                    finally:
                        duration = time.time() - start_time
                        status = "success" if success else "error"

                        # 🔢 Messages consumed (somente se sucesso e operação receive)
                        if success and operation == "receive":
                            KAFKA_MESSAGES_CONSUMED_TOTAL.labels(
                                topic=topic,
                                app_name=APP_NAME,
                            ).inc()

                        # ⏱ Processing duration (sempre)
                        KAFKA_MESSAGE_PROCESSING_DURATION_SECONDS.labels(
                            topic=topic,
                            handler=operation,
                            app_name=APP_NAME,
                            status=status,
                        ).observe(duration)

                        # 🧠 Memory (amostrado)
                        if profile_memory:
                            memory_delta = memory_profiler.get_memory_delta()
                            if memory_delta is not None:
                                KAFKA_CONSUMER_MEMORY_BYTES.labels(
                                    topic=topic,
                                    handler=operation,
                                    app_name=APP_NAME,
                                    status=status,
                                ).observe(abs(memory_delta))

                                if span.is_recording():
                                    span.set_attribute(
                                        "memory.delta_bytes", memory_delta
                                    )

        return wrapper

    return decorator