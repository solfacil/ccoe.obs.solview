"""Tests for SolviewMCPASGIMiddleware — root span per HTTP request."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

from solview.mcp.asgi_middleware import SolviewMCPASGIMiddleware


@pytest.fixture(autouse=True)
def otel_exporter():
    trace._TRACER_PROVIDER_SET_ONCE._done = False
    trace._TRACER_PROVIDER = None

    exporter = InMemorySpanExporter()
    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    trace.set_tracer_provider(provider)
    yield exporter
    exporter.clear()
    provider.shutdown()


@pytest.mark.asyncio
async def test_http_request_creates_root_span_with_method_and_path(otel_exporter):
    async def app(scope, receive, send):
        await send({"type": "http.response.start", "status": 200})
        await send({"type": "http.response.body", "body": b"ok"})

    wrapped = SolviewMCPASGIMiddleware(app)
    scope = {"type": "http", "method": "POST", "path": "/mcp", "scheme": "https"}
    receive = AsyncMock(return_value={"type": "http.request"})
    send = AsyncMock()

    await wrapped(scope, receive, send)

    spans = otel_exporter.get_finished_spans()
    assert len(spans) == 1
    assert spans[0].name == "POST /mcp"
    attrs = dict(spans[0].attributes)
    assert attrs.get("http.request.method") == "POST"
    assert attrs.get("url.path") == "/mcp"
    assert attrs.get("http.response.status_code") == 200


@pytest.mark.asyncio
async def test_non_http_scope_passes_through(otel_exporter):
    async def app(scope, receive, send):
        await send({"type": "lifespan.complete"})

    wrapped = SolviewMCPASGIMiddleware(app)
    scope = {"type": "lifespan"}
    receive = AsyncMock(return_value={"type": "lifespan.startup"})
    send = AsyncMock()

    await wrapped(scope, receive, send)

    spans = otel_exporter.get_finished_spans()
    assert len(spans) == 0


@pytest.mark.asyncio
async def test_exception_sets_span_error_and_status_500(otel_exporter):
    async def app(scope, receive, send):
        raise RuntimeError("fail")

    wrapped = SolviewMCPASGIMiddleware(app)
    scope = {"type": "http", "method": "GET", "path": "/mcp"}
    receive = AsyncMock(return_value={"type": "http.request"})
    send = AsyncMock()

    with pytest.raises(RuntimeError):
        await wrapped(scope, receive, send)

    spans = otel_exporter.get_finished_spans()
    assert len(spans) == 1
    assert spans[0].name == "GET /mcp"
    assert spans[0].status.status_code == trace.StatusCode.ERROR
    attrs = dict(spans[0].attributes)
    assert attrs.get("http.response.status_code") == 500
