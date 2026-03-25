# Validação local – Solview

Instruções resumidas para **subir o ambiente local** e **rodar os principais testes pytest** no seu ambiente, validando as alterações do projeto.

---

## 1. Pré-requisitos

- **Python** 3.9+
- **Docker** e **Docker Compose** (para a stack de observabilidade)
- **Poetry** ou **pip** (instalação do pacote)

```bash
python --version
docker --version
docker-compose --version
```

---

## 2. Instalação do pacote (ambiente local)

Na raiz do repositório:

```bash
# Com Poetry
poetry install

# Ou com pip (editable)
pip install -e ".[dev]"
# Se não houver extras, use:
pip install -e .
```

Para rodar os testes, instale o pytest se ainda não estiver no ambiente:

```bash
pip install pytest pytest-asyncio
```

---

## 3. Variáveis de ambiente

Para a stack e para a aplicação usarem a mesma configuração:

```bash
cp config/solview.env.example .env
```

Ajuste o `.env` se quiser (para desenvolvimento costuma bastar o default).
Para **rodar apenas os testes**, não é obrigatório ter `.env`; os testes que precisam de config usam `setup_settings(SolviewSettings(...))` e/ou `PYTHON_ENV=unittest` (veja a seção de pytest abaixo).

---

## 4. Subir a stack local (Docker Compose)

Na **raiz do repositório**:

```bash
docker-compose up -d
```

Verificar se os serviços subiram:

```bash
docker-compose ps
```

Portas usadas pela stack (evite conflitos):

| Serviço        | Porta | URL local              |
|----------------|-------|------------------------|
| Demo App       | 8000  | http://localhost:8000  |
| Grafana        | 3000  | http://localhost:3000  |
| Prometheus     | 9090  | http://localhost:9090  |
| Loki           | 3100  | http://localhost:3100  |
| Tempo          | 3200  | http://localhost:3200  |
| OTEL Collector | 4317  | gRPC OTLP              |

Credenciais do Grafana (conforme `docker/README.md`): **admin** / **solview123**.

### Validação rápida da stack

```bash
# Health da demo (se o serviço demo estiver no compose)
curl -s http://localhost:8000/ | head -5

# Prometheus
curl -s http://localhost:9090/-/healthy

# Grafana
curl -s -o /dev/null -w "%{http_code}" http://localhost:3000/api/health
```

Para **validar apenas a biblioteca** (tracing, métricas, settings), você **não precisa** subir a stack; basta rodar os pytest. A stack é útil para testar a aplicação demo e a integração com Grafana/Prometheus/Tempo/Loki.

---

## 5. Rodar os principais testes pytest

Na **raiz do repositório**, com o ambiente ativado (Poetry ou venv).

### Todos os testes

```bash
pytest tests/ -v
```

### Por módulo (principais)

```bash
# Tracing (setup_tracer, instrumentação, propagators, protocol)
pytest tests/tracing/ -v

# Métricas (exporters, middleware, core)
pytest tests/metrics/ -v

# Integração (trace, metrics, logging)
pytest tests/integration/ -v

# Logging Solview
pytest tests/solview_logging/ -v
```

### Com cobertura (se tiver pytest-cov)

```bash
pytest tests/ -v --cov=solview --cov-report=term-missing
```

### Ambiente de teste (recomendado para testes de tracing)

Vários testes de tracing usam `PYTHON_ENV=unittest` para usar console exporter em vez de OTLP. O `conftest.py` e os testes já configuram isso onde necessário; em caso de falha em testes de tracing, você pode forçar:

```bash
# Windows (PowerShell)
$env:PYTHON_ENV="unittest"; pytest tests/tracing/ -v

# Windows (cmd)
set PYTHON_ENV=unittest && pytest tests/tracing/ -v

# Linux/macOS
PYTHON_ENV=unittest pytest tests/tracing/ -v
```

---

## 6. Ordem sugerida para validar suas alterações

1. **Só testes (sem Docker)**
   - `pytest tests/ -v`
   - Em especial: `pytest tests/tracing/ tests/metrics/ tests/integration/ -v`

2. **Stack local (opcional)**
   - `docker-compose up -d`
   - Validar health/endpoints acima e, se quiser, acessar Grafana (http://localhost:3000) e Prometheus (http://localhost:9090).

3. **Demo app (opcional)**
   - Se o `docker-compose` sobe uma demo app, acesse http://localhost:8000 e `/metrics`; caso tenha uma app FastAPI local (ex.: `examples/fastapi/main-stg.py`), rode com `uvicorn` e teste `/metrics` e `/health`.

---

## 7. Referência rápida de documentação

- **Stack Docker e cenários**: `docker/README.md`
- **Deploy e setup local**: `docs/deployment-guide.md`
- **Testes e validação**: `docs/testing.md`
- **Config e variáveis**: `config/README.md` e `config/solview.env.example`
