"""HTTP client instrumentation decorators combining OpenTelemetry tracing and Prometheus metrics."""

import inspect
import time
import random
import urllib.parse
from collections.abc import Callable
from functools import wraps

from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode

from solview.config import get_settings
from solview.instrumentation.utils import _normalize_url_path, MemoryProfiler
from solview.metrics.custom import (
    HTTP_OUTGOING_REQUESTS_MEMORY_SAMPLES_TOTAL,
    HTTP_OUTGOING_REQUESTS_TOTAL,
    HTTP_OUTGOING_REQUESTS_DURATION_SECONDS,
    HTTP_OUTGOING_REQUESTS_ERRORS_TOTAL,
    HTTP_OUTGOING_REQUESTS_MEMORY_BYTES,
)
from solview.solview_logging import get_logger

logger = get_logger(__name__)


def _extract_status_code(result, exc: Exception | None = None) -> int | None:
    """Extract HTTP status code from a response object or exception.

    Checks, in order:
    1. ``result.status_code`` (httpx.Response, requests.Response, etc.)
    2. ``exc.response.status_code`` (httpx.HTTPStatusError, requests.HTTPError)
    3. ``exc.status_code`` (custom exception with status_code attr)

    Returns None when the status code cannot be determined.
    """
    for obj in (result, getattr(exc, "response", None), exc):
        if obj is None:
            continue
        code = getattr(obj, "status_code", None)
        if code is not None:
            try:
                return int(code)
            except (TypeError, ValueError):
                continue
    return None


def http_client_instrumentation(operation: str = "request"):
    """
    Decorator to instrument HTTP client operations with tracing and metrics.
    """

    def decorator(func: Callable) -> Callable:
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
            caught_exc: Exception | None = None

            settings = get_settings()
            app_name = settings.service_name
            profile_memory = (
                settings.enable_memory_profiling
                and random.random() < settings.sampling_memory_profiling
            )
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
                    caught_exc = exc
                    span.record_exception(exc)
                    span.set_status(
                        Status(StatusCode.ERROR, description=str(exc))
                    )
                    raise

                finally:
                    duration = time.perf_counter() - start_time

                    status_code = _extract_status_code(result, caught_exc)
                    if not success:
                        status = "error"
                    elif status_code is not None and status_code >= 400:
                        status = "error"
                    else:
                        status = "success"

                    status_code_str = str(status_code) if status_code is not None else "exception"

                    if recording and status_code is not None:
                        span.set_attribute("http.response.status_code", status_code)

                    HTTP_OUTGOING_REQUESTS_TOTAL.labels(
                        method=method,
                        status_code=status_code_str,
                        url_host=url_host,
                        url_path=normalized_path,
                        app_name=app_name,
                        status=status,
                    ).inc()

                    HTTP_OUTGOING_REQUESTS_DURATION_SECONDS.labels(
                        method=method,
                        url_host=url_host,
                        url_path=normalized_path,
                        app_name=app_name,
                        status=status,
                    ).observe(duration)

                    if status == "error":
                        error_type = (
                            status_code_str
                            if status_code is not None
                            else type(caught_exc).__name__
                            if caught_exc is not None
                            else "exception"
                        )
                        HTTP_OUTGOING_REQUESTS_ERRORS_TOTAL.labels(
                            method=method,
                            url_host=url_host,
                            url_path=normalized_path,
                            error_type=error_type,
                            app_name=app_name,
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
                        app_name=app_name,
                    )
        return wrapper
    return decorator

