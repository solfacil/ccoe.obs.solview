from fastapi import FastAPI
from solview.settings import SolviewSettings
from solview.solview_logging import setup_logger
from solview.metrics import SolviewPrometheusMiddleware, prometheus_metrics_response
from solview.tracing import setup_tracer

app = FastAPI()

# Setup do logger estruturado com informações de serviço
setup_logger(SolviewSettings(service_name="example-fastapi"))

# Middleware de métricas Prometheus
app.add_middleware(SolviewPrometheusMiddleware, service_name="example-fastapi")

# Endpoint de métricas
app.add_route("/metrics", prometheus_metrics_response)

# Setup do tracer OpenTelemetry via variáveis de ambiente
setup_tracer(app)

@app.get("/status")
async def status():
    return {"status": "ok"}

@app.post("/echo")
async def echo(data: dict):
    return {"received": data}

