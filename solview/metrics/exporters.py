import logging
import time

from opentelemetry import trace
from prometheus_client import REGISTRY
from prometheus_client.openmetrics.exposition import CONTENT_TYPE_LATEST, generate_latest

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response
from starlette.routing import Match
from starlette.status import HTTP_500_INTERNAL_SERVER_ERROR
from starlette.types import ASGIApp

from .core import (
    METRIC_INFO,
    METRIC_REQUESTS,
    METRIC_RESPONSES,
    METRIC_REQUESTS_PROCESSING_TIME,
    METRIC_EXCEPTIONS,
    METRIC_REQUESTS_IN_PROGRESS,
)

_logger = logging.getLogger("solview.metrics.asgi")


class SolviewPrometheusMiddleware(BaseHTTPMiddleware):
    """
    Middleware Prometheus/ASGI universal (Starlette, FastAPI ou qualquer ASGI).

    Adiciona métricas de requisições, respostas, exceções, latência e exposição via endpoint.
    Integra com OpenTelemetry trace_id em exemplares (exemplar no Prometheus).
    """

    def __init__(self, app: ASGIApp, service_name: str = 'solview-app') -> None:
        super().__init__(app)
        self.service_name = service_name
        # Info Gauge pode ser coletado depois, mas já inicializa para aparecer no scrape
        METRIC_INFO.labels(service_name=self.service_name).set(1)

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        method = request.method
        path, is_handled_path = self.get_path_template(request)
        if not is_handled_path:
            _logger.debug(f"method={method} path={request.url.path} is_handled_path=False")
            return await call_next(request)
        METRIC_REQUESTS_IN_PROGRESS.labels(method=method, path=path, service_name=self.service_name).inc()
        METRIC_REQUESTS.labels(method=method, path=path, service_name=self.service_name).inc()
        before_time = time.perf_counter()
        try:
            response = await call_next(request)
        except BaseException as e:
            status_code = HTTP_500_INTERNAL_SERVER_ERROR
            METRIC_EXCEPTIONS.labels(
                method=method, path=path, exception_type=type(e).__name__, service_name=self.service_name
            ).inc()
            raise e from None
        else:
            status_code = response.status_code
            after_time = time.perf_counter()
            # Exemplar para trace_id do OpenTelemetry, caso esteja disponível
            span = trace.get_current_span()
            trace_id = None
            if span is not None:
                ctx = span.get_span_context()
                if hasattr(ctx, "trace_id") and ctx.trace_id != 0:
                    trace_id = trace.format_trace_id(ctx.trace_id)
            kwargs = {}
            if trace_id:
                kwargs["exemplar"] = {"TraceID": trace_id}
            METRIC_REQUESTS_PROCESSING_TIME.labels(method=method, path=path, service_name=self.service_name).observe(
                after_time - before_time, **kwargs
            )
        finally:
            METRIC_RESPONSES.labels(
                method=method, path=path, status_code=status_code, service_name=self.service_name
            ).inc()
            METRIC_REQUESTS_IN_PROGRESS.labels(method=method, path=path, service_name=self.service_name).dec()
        return response

    @staticmethod
    def get_path_template(request: Request) -> tuple[str, bool]:
        # Busca o template do path, ex: '/item/{id}' em vez de '/item/100'
        for route in request.app.routes:
            match, _ = route.matches(request.scope)
            if match == Match.FULL:
                return getattr(route, 'path', request.url.path), True
        return request.url.path, False


def prometheus_metrics_response(request: Request) -> Response:
    """
    Endpoint pronto para FastAPI/Starlette: use app.add_route("/metrics", prometheus_metrics_response)
    """
    return Response(generate_latest(REGISTRY), headers={'Content-Type': CONTENT_TYPE_LATEST})
