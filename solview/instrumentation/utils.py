"""Utility functions for instrumentation decorators."""

import re
import tracemalloc
from contextlib import contextmanager
from typing import Optional


def _extract_topic_from_args(args, kwargs):
    topic = kwargs.get("topic", "unknown")

    if topic == "unknown" and len(args) > 1:
        candidate = args[1]
        if hasattr(candidate, "topic"):
            topic = candidate.topic
        elif isinstance(candidate, str):
            topic = candidate

    return topic if topic != "unknown" else "all_topics"


def generate_delta_metrics(
    profile_memory,
    memory_profiler,
    recording,
    span,
    status,
    operation,
    memory_samples_total,
    memory_bytes,
    app_name,
):
    if not profile_memory:
        return
    
    memory_samples_total.labels(
        operation=operation,
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
    
    memory_bytes.labels(
            operation=operation,
            app_name=app_name,
            status=status,
        ).observe(delta)
    
    if recording:
        span.set_attribute("memory.delta_bytes", delta)
        span.set_attribute("memory.sampled", True)
        span.set_attribute("memory.delta_ignored", False)
        span.set_attribute("memory.delta_available", True)
        
        
def _get_base_kafka_attributes(topic, operation, system_type):
    return {
        "messaging.system": "kafka",
        f"messaging.{'destination' if system_type == 'producer' else 'source'}": topic,
        "messaging.operation": operation,
    }


def _normalize_url_path(url_path: str) -> str:
    normalized = re.sub(r"/\d+", "/{id}", url_path)
    normalized = re.sub(
        r"/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
        "/{uuid}",
        normalized,
        flags=re.IGNORECASE,
    )
    normalized = re.sub(r"/[a-f0-9]{24}", "/{object_id}", normalized, flags=re.IGNORECASE)
    normalized = re.sub(r"/[a-f0-9]{32}", "/{hash}", normalized, flags=re.IGNORECASE)

    return normalized.split("?")[0]


class MemoryProfiler:
    def __init__(self, enabled: bool = True):
        self.enabled = enabled
        self._start: Optional[int] = None
        self._end: Optional[int] = None

    def start(self):
        if not self.enabled:
            return

        if not tracemalloc.is_tracing():
            tracemalloc.start()

        self._start = tracemalloc.get_traced_memory()[0]

    def stop(self):
        if not self.enabled or self._start is None:
            return

        self._end = tracemalloc.get_traced_memory()[0]

    @contextmanager
    def measure(self):
        if self.enabled:
            self.start()
        try:
            yield self
        finally:
            if self.enabled:
                self.stop()

    def get_memory_delta(self) -> Optional[int]:
        if (
            not self.enabled
            or self._start is None
            or self._end is None
        ):
            return None

        return max(0, self._end - self._start)