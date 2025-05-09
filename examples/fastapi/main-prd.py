# main.py
from fastapi import FastAPI
from solview.solview_logging.core import setup_logger
from solview.solview_logging.settings import LoggingSettings
from solview.metrics import SolviewPrometheusMiddleware, prometheus_metrics_response
from solview.tracing import setup_tracer_from_env
from loguru import logger

cfg = LoggingSettings(
    environment="prd",
    service_name="aplicacao-demo",
    domain="exemplo",
    subdomain="demo",
    version="1.0.0"
)
setup_logger(cfg)

app = FastAPI()

# Métricas
app.add_middleware(SolviewPrometheusMiddleware, service_name="aplicacao-demo")
app.add_route("/metrics", prometheus_metrics_response)

# Tracing
setup_tracer_from_env(app)

@app.get("/")
async def root():
    from opentelemetry.trace import get_current_span, format_trace_id, format_span_id
    span = get_current_span()
    trace_id = format_trace_id(span.get_span_context().trace_id)
    span_id = format_span_id(span.get_span_context().span_id)
    print(f"TID={trace_id} SID={span_id}")
    logger.info("Rota / acionada!")
    return {"msg": "Hello do SolView!", "trace_id": trace_id, "span_id": span_id}