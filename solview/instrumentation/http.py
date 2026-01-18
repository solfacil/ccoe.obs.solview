"""HTTP client instrumentation decorators combining OpenTelemetry tracing and Prometheus metrics."""

import inspect
import time
import random
import urllib.parse
from collections.abc import Callable
from functools import wraps

from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode

from solview.instrumentation.utils import _normalize_url_path, MemoryProfiler
from solview.metrics.custom import (
    HTTP_OUTGOING_REQUESTS_MEMORY_SAMPLES_TOTAL,
    HTTP_OUTGOING_REQUESTS_TOTAL,
    HTTP_OUTGOING_REQUESTS_DURATION_SECONDS,
    HTTP_OUTGOING_REQUESTS_ERRORS_TOTAL,
    HTTP_OUTGOING_REQUESTS_MEMORY_BYTES,
)
from solview.solview_logging import get_logger
from solview.settings import SolviewSettings

logger = get_logger(__name__)
settings = SolviewSettings()
APP_NAME = settings.service_name


def http_client_instrumentation(operation: str = "request"):
    """
    Decorator to instrument HTTP client operations with tracing and metrics.
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
            method,
            url_host,
            url_path,
            app_name,
        ):
            if not profile_memory:
                return
            
            HTTP_OUTGOING_REQUESTS_MEMORY_SAMPLES_TOTAL.labels(
                method=method,
                url_host=url_host,
                url_path=url_path,
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
            
            HTTP_OUTGOING_REQUESTS_MEMORY_BYTES.labels(
                method=method,
                url_host=url_host,
                url_path=url_path,
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

            self = bound.arguments.get("self")
            path = bound.arguments.get("path", "") or bound.arguments.get("url", "")

            full_url = self.base_url + path
            parsed_url = urllib.parse.urlparse(full_url)

            url_host = parsed_url.netloc or "unknown"
            url_path = parsed_url.path or "/"
            normalized_path = _normalize_url_path(url_path)
            method = operation.upper()

            tracer = trace.get_tracer(f"http.client.{func.__module__}")
            start_time = time.perf_counter()
            success = False
            result = None

            profile_memory = should_profile_memory()
            memory_profiler = MemoryProfiler(enabled=profile_memory)

            with tracer.start_as_current_span(
                f"http.client.{operation}",
                attributes={
                    "http.method": method,
                    "http.url": full_url,
                    "http.scheme": parsed_url.scheme,
                    "http.host": url_host,
                    "http.target": (
                        parsed_url.path
                        + ("?" + parsed_url.query if parsed_url.query else "")
                    ),
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
                    span.set_status(
                        Status(StatusCode.ERROR, description=str(exc))
                    )
                    raise

                finally:
                    duration = time.perf_counter() - start_time
                    status = "success" if success else "error"

                    response = getattr(self, "_last_response", None)
                    status_code = (
                        str(response.status_code)
                        if response is not None
                        else "exception"
                    )

                    HTTP_OUTGOING_REQUESTS_TOTAL.labels(
                        method=method,
                        status_code=status_code,
                        url_host=url_host,
                        url_path=normalized_path,
                        app_name=APP_NAME,
                        status=status,
                    ).inc()

                    HTTP_OUTGOING_REQUESTS_DURATION_SECONDS.labels(
                        method=method,
                        url_host=url_host,
                        url_path=normalized_path,
                        app_name=APP_NAME,
                        status=status,
                    ).observe(duration)

                    if not success:
                        HTTP_OUTGOING_REQUESTS_ERRORS_TOTAL.labels(
                            method=method,
                            url_host=url_host,
                            url_path=normalized_path,
                            error_type="exception",
                            app_name=APP_NAME,
                        ).inc()

                    generate_delta_metrics(
                        profile_memory=profile_memory,
                        memory_profiler=memory_profiler,
                        recording=recording,
                        span=span,
                        status=status,
                        method=method,
                        url_host=url_host,
                        url_path=normalized_path,
                        app_name=APP_NAME,
                    )
        return wrapper
    return decorator

