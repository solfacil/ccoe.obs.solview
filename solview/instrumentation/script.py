"""Decorator de instrumentação para scripts e cronjobs com suporte a funções sync e async."""

import inspect
import random
import time
from collections.abc import Callable
from functools import wraps
from typing import Optional

from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode

from solview.config import get_settings
from solview.instrumentation.utils import MemoryProfiler
from solview.metrics.custom import (
    SCRIPT_RUNS_TOTAL,
    SCRIPT_DURATION_SECONDS,
    SCRIPT_LAST_SUCCESS_TIMESTAMP,
    SCRIPT_LAST_RUN_TIMESTAMP,
    SCRIPT_MEMORY_SAMPLES_TOTAL,
    SCRIPT_MEMORY_BYTES,
)
from solview.metrics.pushgateway import push_metrics_to_gateway
from solview.solview_logging import get_logger

logger = get_logger(__name__)


def script_job_instrumentation(
    job_name: str,
    gateway_url: Optional[str] = None,
    grouping_key: Optional[dict] = None,
    gateway_timeout: int = 30,
):
    """
    Decorator para scripts e cronjobs com suporte a funções sync e async.

    Registra métricas Prometheus (contadores, histogramas, timestamps de última
    execução) e um span OpenTelemetry por execução. Se ``gateway_url`` for
    fornecido, faz push automático para o Prometheus Pushgateway após a execução.

    Args:
        job_name: Nome lógico do job (ex: "fatura-sync", "exportacao-diaria").
            Usado como label nas métricas e como job name no Pushgateway.
        gateway_url: URL do Pushgateway (ex: "http://pushgateway:9091").
            Se None, as métricas são registradas localmente mas não enviadas.
        grouping_key: Labels extras para diferenciar instâncias no Pushgateway,
            ex: {"instance": socket.gethostname()}.
        gateway_timeout: Timeout em segundos para o push HTTP.

    Exemplo sync::

        from solview.instrumentation import script_job_instrumentation

        @script_job_instrumentation(
            "limpeza-diaria",
            gateway_url="http://pushgateway:9091",
        )
        def limpar_registros_expirados():
            db.execute("DELETE FROM sessions WHERE expires_at < NOW()")

    Exemplo async::

        @script_job_instrumentation(
            "sync-faturas",
            gateway_url="http://pushgateway:9091",
        )
        async def sincronizar_faturas():
            async for fatura in repo.listar_pendentes():
                await processar(fatura)

    Sem push (registra localmente — use com start_http_server para workers)::

        @script_job_instrumentation("job-interno")
        def processar():
            ...
    """

    def decorator(func: Callable) -> Callable:

        def _record_metrics(
            success: bool,
            duration: float,
            app_name: str,
            profile_memory: bool,
            memory_profiler: MemoryProfiler,
            recording: bool,
            span,
        ) -> None:
            status = "success" if success else "error"

            SCRIPT_RUNS_TOTAL.labels(
                job_name=job_name,
                app_name=app_name,
                status=status,
            ).inc()

            SCRIPT_DURATION_SECONDS.labels(
                job_name=job_name,
                app_name=app_name,
                status=status,
            ).observe(duration)

            SCRIPT_LAST_RUN_TIMESTAMP.labels(
                job_name=job_name,
                app_name=app_name,
            ).set_to_current_time()

            if success:
                SCRIPT_LAST_SUCCESS_TIMESTAMP.labels(
                    job_name=job_name,
                    app_name=app_name,
                ).set_to_current_time()

            if not profile_memory:
                return

            SCRIPT_MEMORY_SAMPLES_TOTAL.labels(
                job_name=job_name,
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

            SCRIPT_MEMORY_BYTES.labels(
                job_name=job_name,
                app_name=app_name,
                status=status,
            ).observe(delta)

            if recording:
                span.set_attribute("memory.delta_bytes", delta)
                span.set_attribute("memory.sampled", True)
                span.set_attribute("memory.delta_ignored", False)
                span.set_attribute("memory.delta_available", True)

        def _push_if_configured() -> None:
            if gateway_url:
                push_metrics_to_gateway(
                    gateway_url=gateway_url,
                    job_name=job_name,
                    grouping_key=grouping_key,
                    timeout=gateway_timeout,
                )

        if inspect.iscoroutinefunction(func):

            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                tracer = trace.get_tracer(f"script.{func.__module__}")
                settings = get_settings()
                app_name = settings.service_name
                profile_memory = (
                    settings.enable_memory_profiling
                    and random.random() < settings.sampling_memory_profiling
                )
                memory_profiler = MemoryProfiler(enabled=profile_memory)
                start_time = time.perf_counter()
                success = False

                with tracer.start_as_current_span(
                    f"script.{job_name}",
                    attributes={
                        "script.job_name": job_name,
                        "script.app_name": app_name,
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
                        span.record_exception(exc)
                        span.set_status(Status(StatusCode.ERROR, description=str(exc)))
                        raise

                    finally:
                        duration = time.perf_counter() - start_time
                        _record_metrics(
                            success, duration, app_name,
                            profile_memory, memory_profiler, recording, span,
                        )
                        _push_if_configured()

            return async_wrapper

        else:

            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                tracer = trace.get_tracer(f"script.{func.__module__}")
                settings = get_settings()
                app_name = settings.service_name
                profile_memory = (
                    settings.enable_memory_profiling
                    and random.random() < settings.sampling_memory_profiling
                )
                memory_profiler = MemoryProfiler(enabled=profile_memory)
                start_time = time.perf_counter()
                success = False

                with tracer.start_as_current_span(
                    f"script.{job_name}",
                    attributes={
                        "script.job_name": job_name,
                        "script.app_name": app_name,
                    },
                ) as span:
                    recording = span.is_recording()
                    if recording:
                        span.set_attribute("memory.sampling.enabled", profile_memory)

                    try:
                        with memory_profiler.measure():
                            result = func(*args, **kwargs)

                        success = True
                        span.set_status(Status(StatusCode.OK))
                        return result

                    except Exception as exc:
                        span.record_exception(exc)
                        span.set_status(Status(StatusCode.ERROR, description=str(exc)))
                        raise

                    finally:
                        duration = time.perf_counter() - start_time
                        _record_metrics(
                            success, duration, app_name,
                            profile_memory, memory_profiler, recording, span,
                        )
                        _push_if_configured()

            return sync_wrapper

    return decorator
