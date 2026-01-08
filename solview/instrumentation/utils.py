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
        self._start_traced = None
        self._end_traced = None

    def start(self):
        if not self.enabled:
            return

        tracemalloc.start()
        self._start_traced = tracemalloc.get_traced_memory()[0]

    def stop(self):
        if not self.enabled:
            return

        self._end_traced = tracemalloc.get_traced_memory()[0]
        tracemalloc.stop()

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
            or self._start_traced is None
            or self._end_traced is None
        ):
            return None

        return self._end_traced - self._start_traced