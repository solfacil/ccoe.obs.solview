"""Tests for script_job_instrumentation decorator — sync and async functions."""

import time
import pytest
from unittest.mock import patch

from solview.settings import SolviewSettings
from solview.config import setup_settings
from solview.instrumentation.script import script_job_instrumentation
from solview.metrics.custom import (
    SCRIPT_RUNS_TOTAL,
    SCRIPT_DURATION_SECONDS,
    SCRIPT_LAST_SUCCESS_TIMESTAMP,
    SCRIPT_LAST_RUN_TIMESTAMP,
    SCRIPT_MEMORY_SAMPLES_TOTAL,
)


@pytest.fixture(autouse=True)
def script_test_settings():
    return setup_settings(
        SolviewSettings(
            service_name="test-script-app",
            enable_memory_profiling=False,
        )
    )


@pytest.fixture
def script_settings_with_memory():
    return setup_settings(
        SolviewSettings(
            service_name="test-script-app",
            enable_memory_profiling=True,
            sampling_memory_profiling=1.0,
        )
    )


# =============================================================================
# Sync — Success
# =============================================================================


class TestScriptJobSyncSuccess:
    def test_returns_result(self):
        @script_job_instrumentation("sync-success-result")
        def job():
            return 42

        assert job() == 42

    def test_increments_runs_total_success(self):
        @script_job_instrumentation("sync-success-counter")
        def job():
            pass

        before = SCRIPT_RUNS_TOTAL.labels(
            job_name="sync-success-counter",
            app_name="test-script-app",
            status="success",
        )._value.get()

        job()

        after = SCRIPT_RUNS_TOTAL.labels(
            job_name="sync-success-counter",
            app_name="test-script-app",
            status="success",
        )._value.get()
        assert after == before + 1

    def test_updates_last_run_timestamp(self):
        @script_job_instrumentation("sync-success-ts-run")
        def job():
            pass

        before = time.time()
        job()
        after = time.time()

        ts = SCRIPT_LAST_RUN_TIMESTAMP.labels(
            job_name="sync-success-ts-run",
            app_name="test-script-app",
        )._value.get()
        assert before <= ts <= after

    def test_updates_last_success_timestamp(self):
        @script_job_instrumentation("sync-success-ts-success")
        def job():
            pass

        before = time.time()
        job()
        after = time.time()

        ts = SCRIPT_LAST_SUCCESS_TIMESTAMP.labels(
            job_name="sync-success-ts-success",
            app_name="test-script-app",
        )._value.get()
        assert before <= ts <= after

    def test_records_duration(self):
        @script_job_instrumentation("sync-success-duration")
        def job():
            pass

        sum_before = SCRIPT_DURATION_SECONDS.labels(
            job_name="sync-success-duration",
            app_name="test-script-app",
            status="success",
        )._sum.get()

        job()

        sum_after = SCRIPT_DURATION_SECONDS.labels(
            job_name="sync-success-duration",
            app_name="test-script-app",
            status="success",
        )._sum.get()
        assert sum_after > sum_before


# =============================================================================
# Sync — Error
# =============================================================================


class TestScriptJobSyncError:
    def test_reraises_exception(self):
        @script_job_instrumentation("sync-error-reraise")
        def job():
            raise ValueError("oops")

        with pytest.raises(ValueError, match="oops"):
            job()

    def test_increments_runs_total_error(self):
        @script_job_instrumentation("sync-error-counter")
        def job():
            raise RuntimeError("fail")

        before = SCRIPT_RUNS_TOTAL.labels(
            job_name="sync-error-counter",
            app_name="test-script-app",
            status="error",
        )._value.get()

        with pytest.raises(RuntimeError):
            job()

        after = SCRIPT_RUNS_TOTAL.labels(
            job_name="sync-error-counter",
            app_name="test-script-app",
            status="error",
        )._value.get()
        assert after == before + 1

    def test_does_not_increment_success_counter(self):
        @script_job_instrumentation("sync-error-no-success")
        def job():
            raise RuntimeError("fail")

        before = SCRIPT_RUNS_TOTAL.labels(
            job_name="sync-error-no-success",
            app_name="test-script-app",
            status="success",
        )._value.get()

        with pytest.raises(RuntimeError):
            job()

        after = SCRIPT_RUNS_TOTAL.labels(
            job_name="sync-error-no-success",
            app_name="test-script-app",
            status="success",
        )._value.get()
        assert after == before

    def test_does_not_update_last_success_timestamp(self):
        @script_job_instrumentation("sync-error-no-success-ts")
        def job():
            raise RuntimeError("fail")

        ts_before = SCRIPT_LAST_SUCCESS_TIMESTAMP.labels(
            job_name="sync-error-no-success-ts",
            app_name="test-script-app",
        )._value.get()

        with pytest.raises(RuntimeError):
            job()

        ts_after = SCRIPT_LAST_SUCCESS_TIMESTAMP.labels(
            job_name="sync-error-no-success-ts",
            app_name="test-script-app",
        )._value.get()
        assert ts_after == ts_before

    def test_updates_last_run_timestamp_on_error(self):
        @script_job_instrumentation("sync-error-run-ts")
        def job():
            raise RuntimeError("fail")

        before = time.time()
        with pytest.raises(RuntimeError):
            job()
        after = time.time()

        ts = SCRIPT_LAST_RUN_TIMESTAMP.labels(
            job_name="sync-error-run-ts",
            app_name="test-script-app",
        )._value.get()
        assert before <= ts <= after


# =============================================================================
# Async — Success
# =============================================================================


class TestScriptJobAsyncSuccess:
    @pytest.mark.asyncio
    async def test_returns_result(self):
        @script_job_instrumentation("async-success-result")
        async def job():
            return "done"

        assert await job() == "done"

    @pytest.mark.asyncio
    async def test_increments_runs_total_success(self):
        @script_job_instrumentation("async-success-counter")
        async def job():
            pass

        before = SCRIPT_RUNS_TOTAL.labels(
            job_name="async-success-counter",
            app_name="test-script-app",
            status="success",
        )._value.get()

        await job()

        after = SCRIPT_RUNS_TOTAL.labels(
            job_name="async-success-counter",
            app_name="test-script-app",
            status="success",
        )._value.get()
        assert after == before + 1

    @pytest.mark.asyncio
    async def test_updates_last_success_timestamp(self):
        @script_job_instrumentation("async-success-ts")
        async def job():
            pass

        before = time.time()
        await job()
        after = time.time()

        ts = SCRIPT_LAST_SUCCESS_TIMESTAMP.labels(
            job_name="async-success-ts",
            app_name="test-script-app",
        )._value.get()
        assert before <= ts <= after


# =============================================================================
# Async — Error
# =============================================================================


class TestScriptJobAsyncError:
    @pytest.mark.asyncio
    async def test_reraises_exception(self):
        @script_job_instrumentation("async-error-reraise")
        async def job():
            raise ValueError("async oops")

        with pytest.raises(ValueError, match="async oops"):
            await job()

    @pytest.mark.asyncio
    async def test_increments_runs_total_error(self):
        @script_job_instrumentation("async-error-counter")
        async def job():
            raise RuntimeError("async fail")

        before = SCRIPT_RUNS_TOTAL.labels(
            job_name="async-error-counter",
            app_name="test-script-app",
            status="error",
        )._value.get()

        with pytest.raises(RuntimeError):
            await job()

        after = SCRIPT_RUNS_TOTAL.labels(
            job_name="async-error-counter",
            app_name="test-script-app",
            status="error",
        )._value.get()
        assert after == before + 1

    @pytest.mark.asyncio
    async def test_does_not_update_last_success_timestamp(self):
        @script_job_instrumentation("async-error-no-success-ts")
        async def job():
            raise RuntimeError("async fail")

        ts_before = SCRIPT_LAST_SUCCESS_TIMESTAMP.labels(
            job_name="async-error-no-success-ts",
            app_name="test-script-app",
        )._value.get()

        with pytest.raises(RuntimeError):
            await job()

        ts_after = SCRIPT_LAST_SUCCESS_TIMESTAMP.labels(
            job_name="async-error-no-success-ts",
            app_name="test-script-app",
        )._value.get()
        assert ts_after == ts_before


# =============================================================================
# Memory Profiling
# =============================================================================


class TestScriptJobMemoryProfiling:
    def test_increments_memory_samples_total(self, script_settings_with_memory):
        @script_job_instrumentation("memory-sync-samples")
        def job():
            return list(range(1000))

        before = SCRIPT_MEMORY_SAMPLES_TOTAL.labels(
            job_name="memory-sync-samples",
            app_name="test-script-app",
        )._value.get()

        job()

        after = SCRIPT_MEMORY_SAMPLES_TOTAL.labels(
            job_name="memory-sync-samples",
            app_name="test-script-app",
        )._value.get()
        assert after == before + 1

    @pytest.mark.asyncio
    async def test_increments_memory_samples_total_async(
        self, script_settings_with_memory
    ):
        @script_job_instrumentation("memory-async-samples")
        async def job():
            return list(range(1000))

        before = SCRIPT_MEMORY_SAMPLES_TOTAL.labels(
            job_name="memory-async-samples",
            app_name="test-script-app",
        )._value.get()

        await job()

        after = SCRIPT_MEMORY_SAMPLES_TOTAL.labels(
            job_name="memory-async-samples",
            app_name="test-script-app",
        )._value.get()
        assert after == before + 1


# =============================================================================
# Pushgateway integration
# =============================================================================


class TestScriptJobPushgateway:
    def test_push_called_when_gateway_url_provided(self):
        with patch(
            "solview.instrumentation.script.push_metrics_to_gateway"
        ) as mock_push:

            @script_job_instrumentation("gw-sync-push", gateway_url="http://gw:9091")
            def job():
                return 42

            result = job()

        assert result == 42
        mock_push.assert_called_once_with(
            gateway_url="http://gw:9091",
            job_name="gw-sync-push",
            grouping_key=None,
            timeout=30,
        )

    def test_no_push_when_gateway_url_none(self):
        with patch(
            "solview.instrumentation.script.push_metrics_to_gateway"
        ) as mock_push:

            @script_job_instrumentation("gw-sync-no-push")
            def job():
                return 1

            job()

        mock_push.assert_not_called()

    def test_push_called_on_error(self):
        with patch(
            "solview.instrumentation.script.push_metrics_to_gateway"
        ) as mock_push:

            @script_job_instrumentation("gw-sync-push-error", gateway_url="http://gw:9091")
            def job():
                raise RuntimeError("fail")

            with pytest.raises(RuntimeError):
                job()

        mock_push.assert_called_once()

    @pytest.mark.asyncio
    async def test_push_called_async(self):
        with patch(
            "solview.instrumentation.script.push_metrics_to_gateway"
        ) as mock_push:

            @script_job_instrumentation(
                "gw-async-push", gateway_url="http://gw:9091"
            )
            async def job():
                return "ok"

            result = await job()

        assert result == "ok"
        mock_push.assert_called_once_with(
            gateway_url="http://gw:9091",
            job_name="gw-async-push",
            grouping_key=None,
            timeout=30,
        )

    def test_passes_custom_grouping_key(self):
        with patch(
            "solview.instrumentation.script.push_metrics_to_gateway"
        ) as mock_push:

            @script_job_instrumentation(
                "gw-grouping",
                gateway_url="http://gw:9091",
                grouping_key={"instance": "pod-1"},
            )
            def job():
                pass

            job()

        mock_push.assert_called_once_with(
            gateway_url="http://gw:9091",
            job_name="gw-grouping",
            grouping_key={"instance": "pod-1"},
            timeout=30,
        )
