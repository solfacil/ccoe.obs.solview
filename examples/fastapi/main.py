from fastapi import FastAPI, HTTPException
import asyncio
import random

### Opeltel
import os


app = FastAPI(title="Microserviço de Pagamentos (Exemplo)")

# ---------------------------------------------------------
# MÁGICA DA OBSERVABILIDADE AQUI
# Inicializa o Instrumentator e expõe o endpoint /metrics
# ---------------------------------------------------------

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

@app.get("/metrics")
def get_metrics():
    # Isso obriga o FastAPI a ler o "Balde Global"
    # que é exatamente onde o OpenTelemetry (PrometheusMetricReader) escreve!
    return Response(
        content=generate_latest(REGISTRY), 
        media_type=CONTENT_TYPE_LATEST
    )

if __name__ == "__main__":
    import uvicorn
    # Execute rodando: python main.py
    uvicorn.run(app, host="0.0.0.0", port=8000)