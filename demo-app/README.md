# 🌟 Solview Demo Application

> **Aplicação demo estruturada para demonstrar o Solview Observability Stack com arquitetura hexagonal e OpenTelemetry real.**

## 🏗️ Arquitetura

Esta aplicação demonstra uma arquitetura limpa e hexagonal com observabilidade completa:

```
demo-app/
├── 📁 src/app/              # Código principal da aplicação
│   ├── 📁 infra/            # Camada de infraestrutura
│   │   ├── 📁 config/       # Configurações
│   │   ├── 📁 http/         # Clientes HTTP
│   │   ├── 📁 api/          # Middlewares de API
│   │   ├── 📁 monitoring/   # Observabilidade (Prometheus, Sentry)
│   │   ├── 📁 data/         # Repositórios e cache
│   │   └── 📁 logging/      # Configuração de logs
│   ├── 📁 application/      # Camada de aplicação
│   │   ├── 📁 common/       # Utilitários comuns
│   │   ├── 📁 rest/         # Endpoints REST
│   │   └── 📁 dependencies/ # Injeção de dependências
│   ├── 📁 domain/           # Camada de domínio
│   │   ├── 📁 catalog/      # Domínio do catálogo
│   │   ├── 📁 cart/         # Domínio do carrinho
│   │   └── 📁 order/        # Domínio de pedidos
│   ├── 📄 server.py         # Servidor FastAPI
│   └── 📄 environment.py    # Configurações de ambiente
├── 📁 src/tests/            # Testes
│   ├── 📁 unit/             # Testes unitários
│   └── 📁 integration/      # Testes de integração
├── 📄 Dockerfile            # Container otimizado
├── 📄 Makefile              # Automação
├── 📄 pyproject.toml        # Configuração do projeto
└── 📄 README.md             # Este arquivo
```

## 🚀 Quick Start

### Pré-requisitos

- Python 3.11+
- Poetry
- Docker (opcional)
- Make (opcional, mas recomendado)

### 1. Setup Inicial

```bash
# Instalar dependências
make install

# Ou manualmente:
poetry install
```

### 2. Executar em Desenvolvimento

```bash
# Modo desenvolvimento com reload
make dev

# Com logs estruturados em DEBUG
make dev-with-logs

# Ou manualmente:
poetry run uvicorn app.server:app --host 0.0.0.0 --port 8000 --reload
```

### 3. Verificar Funcionamento

```bash
# Health check
curl http://localhost:8000/health

# Métricas Prometheus
curl http://localhost:8000/metrics

# Documentação da API
open http://localhost:8000/docs
```

## 🧪 Testes

```bash
# Todos os testes
make test

# Apenas testes unitários
make test-unit

# Apenas testes de integração
make test-integration

# Com coverage
make test-coverage
```

## 🔍 Code Quality

```bash
# Linting
make lint

# Formatação
make format

# Verificar formatação (sem alterar)
make format-check

# Verificação completa para CI/CD
make ci-check
```

## 🐳 Docker

```bash
# Build da imagem
make docker-build

# Executar container
make docker-run

# Parar container
make docker-stop

# Limpar imagens
make docker-clean
```

## 📊 Observabilidade

### Features Implementadas

- ✅ **OpenTelemetry Real**: Traces distribuídos com Service Graph
- ✅ **Logs Estruturados**: JSON com correlation IDs
- ✅ **Métricas Prometheus**: Custom metrics + auto-instrumentation
- ✅ **Health Checks**: Liveness e readiness probes
- ✅ **Solview Integration**: Biblioteca Solview integrada

### Endpoints de Observabilidade

| Endpoint | Descrição |
|----------|-----------|
| `/health` | Health check básico |
| `/ready` | Readiness probe |
| `/metrics` | Métricas Prometheus |
| `/info` | Informações da aplicação |

### Service Graph

A aplicação gera traces que criam um Service Graph mostrando:

```
┌─────────────────┐    HTTP    ┌─────────────────┐
│  demo-app       │ ────────► │  catalog-api    │
│  (FastAPI)      │           │  (simulado)     │
└─────────────────┘           └─────────────────┘
         │
         │ Database
         ▼
┌─────────────────┐
│   redis-cache   │
│   (simulado)    │
└─────────────────┘
```

## 🛠️ API Endpoints

### Catalog Service

```bash
# Listar produtos
GET /api/catalog/products

# Obter produto específico
GET /api/catalog/products/{product_id}

# Buscar produtos
GET /api/catalog/search?q=termo
```

### Cart Service

```bash
# Criar carrinho
POST /api/cart/create

# Adicionar item ao carrinho
POST /api/cart/{cart_id}/items

# Obter carrinho
GET /api/cart/{cart_id}

# Finalizar carrinho
POST /api/cart/{cart_id}/checkout
```

### Order Service

```bash
# Criar pedido
POST /api/orders

# Obter pedido
GET /api/orders/{order_id}

# Listar pedidos
GET /api/orders
```

## 🔧 Configuração

### Variáveis de Ambiente

```bash
# Aplicação
SOLVIEW_SERVICE_NAME=solview-demo-app
SOLVIEW_VERSION=1.0.0
SOLVIEW_ENVIRONMENT=development
SOLVIEW_LOG_LEVEL=INFO

# OpenTelemetry
OTEL_SERVICE_NAME=solview-demo-app
OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector:4317
OTEL_RESOURCE_ATTRIBUTES=service.name=solview-demo-app

# Infraestrutura
REDIS_URL=redis://localhost:6379
DATABASE_URL=postgresql://user:pass@localhost/db
```

## 📈 Performance & Load Testing

```bash
# Teste de carga simples
make load-test

# Gerar traces para Service Graph
make traces-test
```

## 🚀 Deploy & Production

### Verificação de Produção

```bash
# Verificar se está pronto para produção
make production-check
```

### Deploy com Docker

```bash
# Build e deploy
make docker-build
docker run -d \
  --name solview-demo-app \
  -p 8000:8000 \
  -e SOLVIEW_ENVIRONMENT=production \
  -e OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector:4317 \
  solview-demo-app:latest
```

## 🔗 Integração com LGTM Stack

Para usar com o stack completo do Solview:

```bash
# No diretório raiz do projeto
cd ../
docker-compose up -d

# A aplicação estará integrada com:
# - ✅ Loki (logs)
# - ✅ Grafana (visualização)
# - ✅ Tempo (traces)
# - ✅ Prometheus (métricas)
```

## 🤝 Contributing

1. Fork o projeto
2. Crie uma branch (`git checkout -b feature/nova-feature`)
3. Commit suas mudanças (`git commit -am 'Add nova feature'`)
4. Push para a branch (`git push origin feature/nova-feature`)
5. Abra um Pull Request

## 📝 License

Este projeto é parte do Solview Observability Stack - CCOE Platform Team.
