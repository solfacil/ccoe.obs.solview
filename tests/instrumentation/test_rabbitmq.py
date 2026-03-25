"""Tests for rabbitmq_publisher_instrumentation and rabbitmq_consumer_instrumentation decorators."""

import pytest

from solview.settings import SolviewSettings
from solview.config import setup_settings
from solview.instrumentation.rabbitmq import (
    rabbitmq_publisher_instrumentation,
    rabbitmq_consumer_instrumentation,
)
from solview.metrics.custom import (
    RABBITMQ_MESSAGES_PUBLISHED_TOTAL,
    RABBITMQ_PUBLISHER_DURATION_SECONDS,
    RABBITMQ_PUBLISHER_ERRORS_TOTAL,
    RABBITMQ_PUBLISHER_MEMORY_SAMPLES_TOTAL,
    RABBITMQ_MESSAGES_CONSUMED_TOTAL,
    RABBITMQ_CONSUMER_PROCESSING_DURATION_SECONDS,
    RABBITMQ_CONSUMER_ERRORS_TOTAL,
    RABBITMQ_CONSUMER_MEMORY_SAMPLES_TOTAL,
    RABBITMQ_CONSUMER_LAST_SUCCESS_TIMESTAMP,
    RABBITMQ_CONSUMER_CONSECUTIVE_ERRORS,
)


@pytest.fixture(autouse=True)
def rabbitmq_test_settings():
    return setup_settings(
        SolviewSettings(
            service_name="test-rabbitmq-app",
            enable_memory_profiling=False,
        )
    )


@pytest.fixture
def rabbitmq_settings_with_memory():
    return setup_settings(
        SolviewSettings(
            service_name="test-rabbitmq-app",
            enable_memory_profiling=True,
            sampling_memory_profiling=1.0,
        )
    )


# =============================================================================
# Publisher Tests
# =============================================================================


class TestRabbitMQPublisherSuccess:
    @pytest.mark.asyncio
    async def test_returns_result(self):
        @rabbitmq_publisher_instrumentation(operation="publish")
        async def publish_msg(exchange: str, routing_key: str, body: bytes):
            return "published"

        result = await publish_msg(
            exchange="events", routing_key="order.created", body=b"test"
        )
        assert result == "published"

    @pytest.mark.asyncio
    async def test_increments_published_total(self):
        @rabbitmq_publisher_instrumentation(operation="publish")
        async def publish_msg(exchange: str, routing_key: str, body: bytes):
            return None

        metric = RABBITMQ_MESSAGES_PUBLISHED_TOTAL.labels(
            routing_key="order.pub_total",
            exchange="events_pub_total",
            app_name="test-rabbitmq-app",
        )
        before = metric._value.get()

        await publish_msg(
            exchange="events_pub_total", routing_key="order.pub_total", body=b"data"
        )

        assert metric._value.get() == before + 1

    @pytest.mark.asyncio
    async def test_observes_duration(self):
        @rabbitmq_publisher_instrumentation(operation="publish")
        async def publish_msg(exchange: str, routing_key: str, body: bytes):
            return None

        metric = RABBITMQ_PUBLISHER_DURATION_SECONDS.labels(
            routing_key="order.dur",
            exchange="events_dur",
            app_name="test-rabbitmq-app",
            status="success",
        )
        before = metric._sum.get()

        await publish_msg(exchange="events_dur", routing_key="order.dur", body=b"data")

        assert metric._sum.get() > before


class TestRabbitMQPublisherError:
    @pytest.mark.asyncio
    async def test_propagates_exception(self):
        @rabbitmq_publisher_instrumentation(operation="publish")
        async def publish_msg(exchange: str, routing_key: str, body: bytes):
            raise ConnectionError("RabbitMQ unreachable")

        with pytest.raises(ConnectionError, match="RabbitMQ unreachable"):
            await publish_msg(exchange="ex", routing_key="rk", body=b"data")

    @pytest.mark.asyncio
    async def test_increments_error_counter(self):
        @rabbitmq_publisher_instrumentation(operation="publish")
        async def publish_msg(exchange: str, routing_key: str, body: bytes):
            raise TimeoutError("timeout")

        error_metric = RABBITMQ_PUBLISHER_ERRORS_TOTAL.labels(
            routing_key="rk_err",
            exchange="ex_err",
            error_type="TimeoutError",
            app_name="test-rabbitmq-app",
        )
        before = error_metric._value.get()

        with pytest.raises(TimeoutError):
            await publish_msg(exchange="ex_err", routing_key="rk_err", body=b"data")

        assert error_metric._value.get() == before + 1

    @pytest.mark.asyncio
    async def test_observes_duration_on_error(self):
        @rabbitmq_publisher_instrumentation(operation="publish")
        async def publish_msg(exchange: str, routing_key: str, body: bytes):
            raise RuntimeError("fail")

        metric = RABBITMQ_PUBLISHER_DURATION_SECONDS.labels(
            routing_key="rk_dur_err",
            exchange="ex_dur_err",
            app_name="test-rabbitmq-app",
            status="error",
        )
        before = metric._sum.get()

        with pytest.raises(RuntimeError):
            await publish_msg(
                exchange="ex_dur_err", routing_key="rk_dur_err", body=b"data"
            )

        assert metric._sum.get() > before


class TestRabbitMQPublisherMemoryProfiling:
    @pytest.mark.asyncio
    async def test_memory_samples_incremented(self, rabbitmq_settings_with_memory):
        @rabbitmq_publisher_instrumentation(operation="publish")
        async def publish_msg(exchange: str, routing_key: str, body: bytes):
            return None

        metric = RABBITMQ_PUBLISHER_MEMORY_SAMPLES_TOTAL.labels(
            routing_key="rk_mem", exchange="ex_mem", app_name="test-rabbitmq-app"
        )
        before = metric._value.get()

        await publish_msg(exchange="ex_mem", routing_key="rk_mem", body=b"data")

        assert metric._value.get() == before + 1

    @pytest.mark.asyncio
    async def test_no_memory_when_disabled(self):
        @rabbitmq_publisher_instrumentation(operation="publish")
        async def publish_msg(exchange: str, routing_key: str, body: bytes):
            return None

        metric = RABBITMQ_PUBLISHER_MEMORY_SAMPLES_TOTAL.labels(
            routing_key="rk_no_mem", exchange="ex_no_mem", app_name="test-rabbitmq-app"
        )
        before = metric._value.get()

        await publish_msg(exchange="ex_no_mem", routing_key="rk_no_mem", body=b"data")

        assert metric._value.get() == before


# =============================================================================
# Consumer Tests
# =============================================================================


class TestRabbitMQConsumerSuccess:
    @pytest.mark.asyncio
    async def test_returns_result(self):
        @rabbitmq_consumer_instrumentation(operation="process")
        async def process_msg(queue: str, body: bytes):
            return "processed"

        result = await process_msg(queue="orders", body=b"test")
        assert result == "processed"

    @pytest.mark.asyncio
    async def test_observes_duration(self):
        @rabbitmq_consumer_instrumentation(operation="process")
        async def process_msg(queue: str, body: bytes):
            return None

        metric = RABBITMQ_CONSUMER_PROCESSING_DURATION_SECONDS.labels(
            queue="orders_dur",
            handler="process",
            app_name="test-rabbitmq-app",
            status="success",
        )
        before = metric._sum.get()

        await process_msg(queue="orders_dur", body=b"data")

        assert metric._sum.get() > before

    @pytest.mark.asyncio
    async def test_increments_consumed_total_on_receive(self):
        @rabbitmq_consumer_instrumentation(operation="receive")
        async def receive_msg(queue: str, body: bytes):
            return None

        metric = RABBITMQ_MESSAGES_CONSUMED_TOTAL.labels(
            queue="orders_recv", app_name="test-rabbitmq-app"
        )
        before = metric._value.get()

        await receive_msg(queue="orders_recv", body=b"data")

        assert metric._value.get() == before + 1


class TestRabbitMQConsumerError:
    @pytest.mark.asyncio
    async def test_propagates_exception(self):
        @rabbitmq_consumer_instrumentation(operation="process")
        async def process_msg(queue: str, body: bytes):
            raise ValueError("invalid message")

        with pytest.raises(ValueError, match="invalid message"):
            await process_msg(queue="orders", body=b"bad")

    @pytest.mark.asyncio
    async def test_increments_error_counter(self):
        @rabbitmq_consumer_instrumentation(operation="process")
        async def process_msg(queue: str, body: bytes):
            raise TimeoutError("timeout")

        error_metric = RABBITMQ_CONSUMER_ERRORS_TOTAL.labels(
            queue="orders_err", error_type="TimeoutError", app_name="test-rabbitmq-app"
        )
        before = error_metric._value.get()

        with pytest.raises(TimeoutError):
            await process_msg(queue="orders_err", body=b"data")

        assert error_metric._value.get() == before + 1

    @pytest.mark.asyncio
    async def test_observes_duration_on_error(self):
        @rabbitmq_consumer_instrumentation(operation="process")
        async def process_msg(queue: str, body: bytes):
            raise RuntimeError("fail")

        metric = RABBITMQ_CONSUMER_PROCESSING_DURATION_SECONDS.labels(
            queue="orders_dur_err",
            handler="process",
            app_name="test-rabbitmq-app",
            status="error",
        )
        before = metric._sum.get()

        with pytest.raises(RuntimeError):
            await process_msg(queue="orders_dur_err", body=b"data")

        assert metric._sum.get() > before


class TestRabbitMQConsumerMemoryProfiling:
    @pytest.mark.asyncio
    async def test_memory_samples_incremented(self, rabbitmq_settings_with_memory):
        @rabbitmq_consumer_instrumentation(operation="process")
        async def process_msg(queue: str, body: bytes):
            return None

        metric = RABBITMQ_CONSUMER_MEMORY_SAMPLES_TOTAL.labels(
            queue="orders_mem", handler="process", app_name="test-rabbitmq-app"
        )
        before = metric._value.get()

        await process_msg(queue="orders_mem", body=b"data")

        assert metric._value.get() == before + 1

    @pytest.mark.asyncio
    async def test_no_memory_when_disabled(self):
        @rabbitmq_consumer_instrumentation(operation="process")
        async def process_msg(queue: str, body: bytes):
            return None

        metric = RABBITMQ_CONSUMER_MEMORY_SAMPLES_TOTAL.labels(
            queue="orders_no_mem", handler="process", app_name="test-rabbitmq-app"
        )
        before = metric._value.get()

        await process_msg(queue="orders_no_mem", body=b"data")

        assert metric._value.get() == before


class TestRabbitMQMultipleQueues:
    @pytest.mark.asyncio
    async def test_different_queues_have_separate_metrics(self):
        @rabbitmq_consumer_instrumentation(operation="process")
        async def process_orders(queue: str, body: bytes):
            pass

        @rabbitmq_consumer_instrumentation(operation="process")
        async def process_notifications(queue: str, body: bytes):
            pass

        orders_metric = RABBITMQ_CONSUMER_PROCESSING_DURATION_SECONDS.labels(
            queue="orders_multi",
            handler="process",
            app_name="test-rabbitmq-app",
            status="success",
        )
        notifications_metric = RABBITMQ_CONSUMER_PROCESSING_DURATION_SECONDS.labels(
            queue="notifications_multi",
            handler="process",
            app_name="test-rabbitmq-app",
            status="success",
        )

        orders_before = orders_metric._sum.get()
        notifications_before = notifications_metric._sum.get()

        await process_orders(queue="orders_multi", body=b"data")
        await process_notifications(queue="notifications_multi", body=b"data")

        assert orders_metric._sum.get() > orders_before
        assert notifications_metric._sum.get() > notifications_before


# =============================================================================
# Resilience Metrics Tests
# =============================================================================


class TestRabbitMQConsumerResilience:
    @pytest.mark.asyncio
    async def test_last_success_timestamp_updated_on_success(self):
        @rabbitmq_consumer_instrumentation(operation="process")
        async def process_msg(queue: str, body: bytes):
            return None

        metric = RABBITMQ_CONSUMER_LAST_SUCCESS_TIMESTAMP.labels(
            queue="orders_resil_ts", app_name="test-rabbitmq-app"
        )
        before = metric._value.get()

        await process_msg(queue="orders_resil_ts", body=b"data")

        assert metric._value.get() > before

    @pytest.mark.asyncio
    async def test_consecutive_errors_resets_on_success(self):
        @rabbitmq_consumer_instrumentation(operation="process")
        async def process_msg(queue: str, body: bytes):
            return None

        metric = RABBITMQ_CONSUMER_CONSECUTIVE_ERRORS.labels(
            queue="orders_resil_reset", app_name="test-rabbitmq-app"
        )
        metric.set(5)

        await process_msg(queue="orders_resil_reset", body=b"data")

        assert metric._value.get() == 0

    @pytest.mark.asyncio
    async def test_consecutive_errors_increments_on_error(self):
        @rabbitmq_consumer_instrumentation(operation="process")
        async def process_msg(queue: str, body: bytes):
            raise RuntimeError("fail")

        metric = RABBITMQ_CONSUMER_CONSECUTIVE_ERRORS.labels(
            queue="orders_resil_inc", app_name="test-rabbitmq-app"
        )
        before = metric._value.get()

        with pytest.raises(RuntimeError):
            await process_msg(queue="orders_resil_inc", body=b"data")

        assert metric._value.get() == before + 1

    @pytest.mark.asyncio
    async def test_consecutive_errors_accumulates(self):
        @rabbitmq_consumer_instrumentation(operation="process")
        async def process_msg(queue: str, body: bytes):
            raise RuntimeError("fail")

        metric = RABBITMQ_CONSUMER_CONSECUTIVE_ERRORS.labels(
            queue="orders_resil_accum", app_name="test-rabbitmq-app"
        )
        metric.set(0)

        for _ in range(3):
            with pytest.raises(RuntimeError):
                await process_msg(queue="orders_resil_accum", body=b"data")

        assert metric._value.get() == 3

    @pytest.mark.asyncio
    async def test_last_success_not_updated_on_error(self):
        @rabbitmq_consumer_instrumentation(operation="process")
        async def process_msg(queue: str, body: bytes):
            raise RuntimeError("fail")

        metric = RABBITMQ_CONSUMER_LAST_SUCCESS_TIMESTAMP.labels(
            queue="orders_resil_no_ts", app_name="test-rabbitmq-app"
        )
        before = metric._value.get()

        with pytest.raises(RuntimeError):
            await process_msg(queue="orders_resil_no_ts", body=b"data")

        assert metric._value.get() == before
