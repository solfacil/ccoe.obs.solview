"""
Middleware ASGI que cria um span raiz por request HTTP para servidores MCP.

Quando o servidor MCP é exposto via HTTP (ex.: POST /mcp), sem um span raiz por request
a primeira operação executada (ex.: Redis SETEX do cache) vira a raiz do trace e o nome
do trace fica incorreto (ex.: "mcp-distribution SETEX"). Este middleware deve ser
aplicado como camada mais externa do app ASGI para que cada request tenha um span raiz
com nome no formato "METHOD path" (ex.: "POST /mcp"), e as operações MCP/Redis fiquem
como filhos desse span.
"""

from __future__ import annotations

import typing

from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode

from solview.solview_logging import get_logger

logger = get_logger(__name__)

if typing.TYPE_CHECKING:
    from typing import Any, Awaitable, Callable

    Scope = dict[str, Any]
    Receive = Callable[[], Awaitable[dict[str, Any]]]
    Send = Callable[[dict[str, Any]], Awaitable[None]]


# Atributos HTTP (semconv) para compatibilidade com backends
HTTP_METHOD = "http.request.method"
HTTP_SCHEME = "url.scheme"
URL_PATH = "url.path"
URL_QUERY = "url.query"
HTTP_RESPONSE_STATUS_CODE = "http.response.status_code"


def _span_name_from_scope(scope: Scope) -> str:
    method = scope.get("method", "GET").upper()
    path = scope.get("path") or "/"
    return f"{method} {path}"


class SolviewMCPASGIMiddleware:
    """
    Middleware ASGI que cria um span raiz por request HTTP para servidores MCP.

    Use como camada mais externa do app ASGI para que o trace tenha um span raiz
    por request (ex.: "POST /mcp") em vez da primeira operação (ex.: Redis SETEX).

    Uso típico com FastMCP (quando o framework expõe o app ASGI)::

        from fastmcp import FastMCP
        from solview.mcp import SolviewMCPMiddleware, SolviewMCPASGIMiddleware

        mcp = FastMCP("MeuServidor")
        mcp.add_middleware(SolviewMCPMiddleware())
        app = mcp.get_asgi_app()  # ou como seu framework expõe o app
        app = SolviewMCPASGIMiddleware(app)
        uvicorn.run(app, host="0.0.0.0", port=8000)
    """

    def __init__(
        self, app: typing.Callable[[Scope, Receive, Send], typing.Awaitable[None]]
    ) -> None:
        self.app = app
        self._tracer = trace.get_tracer("solview.mcp.asgi", "1.0.0")

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope.get("type") != "http":
            await self.app(scope, receive, send)
            return

        span_name = _span_name_from_scope(scope)
        attrs: dict[str, str | int] = {
            HTTP_METHOD: scope.get("method", "GET"),
            URL_PATH: scope.get("path") or "/",
        }
        if scope.get("query_string"):
            attrs[URL_QUERY] = scope.get("query_string", b"").decode("latin-1")
        if scope.get("scheme"):
            attrs[HTTP_SCHEME] = scope.get("scheme", "http")

        status_code: int | None = None

        async def send_wrapper(message: dict[str, typing.Any]) -> None:
            nonlocal status_code
            if status_code is None and message.get("type") == "http.response.start":
                status_code = message.get("status", 500)
                if span.is_recording():
                    span.set_attribute(HTTP_RESPONSE_STATUS_CODE, status_code)
                if status_code >= 400:
                    span.set_status(
                        Status(StatusCode.ERROR, description=f"HTTP {status_code}")
                    )
                else:
                    span.set_status(Status(StatusCode.OK))
            await send(message)

        with self._tracer.start_as_current_span(
            span_name,
            kind=trace.SpanKind.SERVER,
            attributes=attrs,
        ) as span:
            try:
                await self.app(scope, receive, send_wrapper)
            except Exception as exc:
                if span.is_recording():
                    span.record_exception(exc)
                span.set_status(Status(StatusCode.ERROR, description=str(exc)))
                if status_code is None:
                    span.set_attribute(HTTP_RESPONSE_STATUS_CODE, 500)
                raise
