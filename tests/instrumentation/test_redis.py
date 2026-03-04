"""Tests for redis_client_instrumentation decorator."""

import pytest
from unittest.mock import AsyncMock

from solview.settings import SolviewSettings
from solview.config import setup_settings
from solview.instrumentation.redis import redis_client_instrumentation
from solview.metrics.custom import (
    REDIS_OPERATIONS_TOTAL,
    REDIS_OPERATIONS_DURATION_SECONDS,
    REDIS_OPERATIONS_ERRORS_TOTAL,
    REDIS_OPERATIONS_MEMORY_SAMPLES_TOTAL,
)


@pytest.fixture(autouse=True)
def redis_test_settings():
    return setup_settings(
        SolviewSettings(
            service_name="test-redis-app",
            enable_memory_profiling=False,
        )
    )


@pytest.fixture
def redis_settings_with_memory():
    return setup_settings(
        SolviewSettings(
            service_name="test-redis-app",
            enable_memory_profiling=True,
            sampling_memory_profiling=1.0,
        )
    )


class TestRedisClientInstrumentationSuccess:

    @pytest.mark.asyncio
    async def test_returns_result(self):
        @redis_client_instrumentation(command="get")
        async def get_key(key: str):
            return "cached_value"

        result = await get_key("user:123")
        assert result == "cached_value"

    @pytest.mark.asyncio
    async def test_increments_total_counter(self):
        @redis_client_instrumentation(command="get_counter_test")
        async def get_key(key: str):
            return "val"

        metric = REDIS_OPERATIONS_TOTAL.labels(
            command="get_counter_test", app_name="test-redis-app", status="success"
        )
        before = metric._value.get()

        await get_key("k")

        assert metric._value.get() == before + 1

    @pytest.mark.asyncio
    async def test_observes_duration(self):
        @redis_client_instrumentation(command="get_duration_test")
        async def get_key(key: str):
            return "val"

        metric = REDIS_OPERATIONS_DURATION_SECONDS.labels(
            command="get_duration_test", app_name="test-redis-app", status="success"
        )
        before = metric._sum.get()

        await get_key("k")

        assert metric._sum.get() > before


class TestRedisClientInstrumentationError:

    @pytest.mark.asyncio
    async def test_propagates_exception(self):
        @redis_client_instrumentation(command="get_err")
        async def get_key(key: str):
            raise ConnectionError("Redis unreachable")

        with pytest.raises(ConnectionError, match="Redis unreachable"):
            await get_key("k")

    @pytest.mark.asyncio
    async def test_increments_error_counter(self):
        @redis_client_instrumentation(command="get_err_counter")
        async def get_key(key: str):
            raise TimeoutError("timeout")

        error_metric = REDIS_OPERATIONS_ERRORS_TOTAL.labels(
            command="get_err_counter", error_type="TimeoutError", app_name="test-redis-app"
        )
        before = error_metric._value.get()

        with pytest.raises(TimeoutError):
            await get_key("k")

        assert error_metric._value.get() == before + 1

    @pytest.mark.asyncio
    async def test_increments_total_with_error_status(self):
        @redis_client_instrumentation(command="get_total_err")
        async def get_key(key: str):
            raise ValueError("bad")

        metric = REDIS_OPERATIONS_TOTAL.labels(
            command="get_total_err", app_name="test-redis-app", status="error"
        )
        before = metric._value.get()

        with pytest.raises(ValueError):
            await get_key("k")

        assert metric._value.get() == before + 1

    @pytest.mark.asyncio
    async def test_observes_duration_on_error(self):
        @redis_client_instrumentation(command="get_dur_err")
        async def get_key(key: str):
            raise RuntimeError("fail")

        metric = REDIS_OPERATIONS_DURATION_SECONDS.labels(
            command="get_dur_err", app_name="test-redis-app", status="error"
        )
        before = metric._sum.get()

        with pytest.raises(RuntimeError):
            await get_key("k")

        assert metric._sum.get() > before


class TestRedisMemoryProfiling:

    @pytest.mark.asyncio
    async def test_memory_samples_incremented(self, redis_settings_with_memory):
        @redis_client_instrumentation(command="get_mem")
        async def get_key(key: str):
            return "val"

        metric = REDIS_OPERATIONS_MEMORY_SAMPLES_TOTAL.labels(
            command="get_mem", app_name="test-redis-app"
        )
        before = metric._value.get()

        await get_key("k")

        assert metric._value.get() == before + 1

    @pytest.mark.asyncio
    async def test_no_memory_when_disabled(self):
        @redis_client_instrumentation(command="get_no_mem")
        async def get_key(key: str):
            return "val"

        metric = REDIS_OPERATIONS_MEMORY_SAMPLES_TOTAL.labels(
            command="get_no_mem", app_name="test-redis-app"
        )
        before = metric._value.get()

        await get_key("k")

        assert metric._value.get() == before


class TestRedisMultipleCommands:

    @pytest.mark.asyncio
    async def test_different_commands_have_separate_metrics(self):
        @redis_client_instrumentation(command="set")
        async def set_key(key: str, value: str):
            pass

        @redis_client_instrumentation(command="del")
        async def del_key(key: str):
            pass

        set_metric = REDIS_OPERATIONS_TOTAL.labels(
            command="set", app_name="test-redis-app", status="success"
        )
        del_metric = REDIS_OPERATIONS_TOTAL.labels(
            command="del", app_name="test-redis-app", status="success"
        )

        set_before = set_metric._value.get()
        del_before = del_metric._value.get()

        await set_key("k", "v")
        await del_key("k")

        assert set_metric._value.get() == set_before + 1
        assert del_metric._value.get() == del_before + 1
