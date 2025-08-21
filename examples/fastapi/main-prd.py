# main.py
from fastapi import FastAPI
from solview import SolviewSettings, setup_logger, setup_tracer, get_logger
from solview.metrics import SolviewPrometheusMiddleware, prometheus_metrics_response

settings = SolviewSettings(
    environment="prd",
    service_name="aplicacao-demo",
    domain="exemplo",
    subdomain="demo",
    version="1.0.0",
)
setup_logger(settings)
logger = get_logger(__name__)

app = FastAPI()

# Métricas
app.add_middleware(SolviewPrometheusMiddleware, settings=settings)
app.add_route("/metrics", prometheus_metrics_response)

# Tracing
setup_tracer(settings, app)

@app.get("/")
async def root():
    from opentelemetry.trace import get_current_span, format_trace_id, format_span_id
    span = get_current_span()
    ctx = span.get_span_context()
    trace_id = format_trace_id(ctx.trace_id)
    span_id = format_span_id(ctx.span_id)
    logger.info("Rota / acionada!", trace_id=trace_id, span_id=span_id)
    return {"msg": "Hello do SolView!", "trace_id": trace_id, "span_id": span_id}