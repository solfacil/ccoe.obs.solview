from fastapi import FastAPI
from solview import SolviewSettings, setup_logger, setup_tracer
from solview.metrics import SolviewPrometheusMiddleware, prometheus_metrics_response

app = FastAPI()

# Settings e logger estruturado
settings = SolviewSettings(service_name="example-fastapi", environment="stg")
setup_logger(settings)

# Middleware de métricas Prometheus (via settings)
app.add_middleware(SolviewPrometheusMiddleware, settings=settings)

# Endpoint de métricas
app.add_route("/metrics", prometheus_metrics_response)

# Setup do tracer OpenTelemetry com settings
setup_tracer(settings, app)

@app.get("/status")
async def status():
    return {"status": "ok"}

@app.post("/echo")
async def echo(data: dict):
    return {"received": data}

