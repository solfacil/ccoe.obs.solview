# main.py
from fastapi import FastAPI
from fastapi import HTTPException
from solview import (
    SolviewSettings,
    setup_logger,
    setup_tracer,
    setup_settings,
    get_logger,
)
from solview.metrics import SolviewPrometheusMiddleware, prometheus_metrics_response
import random
import asyncio
import httpx

settings = SolviewSettings(
    environment="prd",
    service_name="aplicacao-demo",
    domain="exemplo",
    subdomain="demo",
    version="1.0.0",
)
setup_settings(settings)
setup_logger(settings)
logger = get_logger(__name__)

app = FastAPI()

# Métricas
app.add_middleware(SolviewPrometheusMiddleware, settings=settings)
app.add_route("/metrics", prometheus_metrics_response)

# Tracing (usa get_settings() internamente)
setup_tracer(app)


@app.get("/")
async def root():
    return {"status": "ok", "message": "Serviço no ar!"}


def fake_tempo_processamento():
    return random.uniform(0.1, 1.5)


@app.get("/processar")
async def processar_dados():
    # Simula um endpoint com tempo de resposta variável (Duration)
    tempo_processamento = fake_tempo_processamento()
    await asyncio.sleep(tempo_processamento)
    return {"message": f"Processado em {tempo_processamento:.2f}s"}


@app.get("/falha")
async def simular_erro():
    # Simula um endpoint que gera erros 500 aleatoriamente (Errors)
    if random.random() > 0.5:
        raise HTTPException(status_code=500, detail="Conexão com o banco falhou!")
    return {"message": "Passou sem erro desta vez."}


@app.get("/http")
async def http_request():
    try:
        async with httpx.AsyncClient(verify=False) as client:
            response = await client.get(
                url="https://jsonplaceholder.typicode.com/posts",
            )

    except (httpx.HTTPError, httpx.TimeoutException, AttributeError, TypeError) as err:
        raise HTTPException(status_code=500, detail=str(err))

    return response.json()
