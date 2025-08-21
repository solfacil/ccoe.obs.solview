# =============================================================================
# 🛠️  SOLVIEW DEMO APP - MAKEFILE
# =============================================================================
# Automação para desenvolvimento, build, teste e deploy
# =============================================================================

.PHONY: help install dev test lint format build run clean docker-build docker-run docker-stop docker-clean

# 📋 Help
help: ## Mostrar ajuda
	@echo "🌟 Solview Demo App - Comandos Disponíveis:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'
	@echo ""

# 🏗️  Development
install: ## Instalar dependências
	@echo "📦 Instalando dependências..."
	poetry install
	pre-commit install

dev: ## Executar em modo desenvolvimento
	@echo "🚀 Iniciando aplicação em modo desenvolvimento..."
	poetry run uvicorn app.server:app --host 0.0.0.0 --port 8000 --reload

dev-with-logs: ## Executar com logs estruturados
	@echo "🚀 Iniciando aplicação com logs estruturados..."
	SOLVIEW_LOG_LEVEL=DEBUG poetry run uvicorn app.server:app --host 0.0.0.0 --port 8000 --reload

# 🧪 Testing
test: ## Executar todos os testes
	@echo "🧪 Executando testes..."
	poetry run pytest src/tests/ -v

test-unit: ## Executar testes unitários
	@echo "🧪 Executando testes unitários..."
	poetry run pytest src/tests/unit/ -v

test-integration: ## Executar testes de integração
	@echo "🧪 Executando testes de integração..."
	poetry run pytest src/tests/integration/ -v

test-coverage: ## Executar testes com coverage
	@echo "🧪 Executando testes com coverage..."
	poetry run pytest --cov=src/app --cov-report=html --cov-report=term-missing

# 🔍 Code Quality
lint: ## Executar linting
	@echo "🔍 Executando linting..."
	poetry run flake8 src/
	poetry run mypy src/app/

format: ## Formatar código
	@echo "✨ Formatando código..."
	poetry run black src/
	poetry run isort src/

format-check: ## Verificar formatação
	@echo "✨ Verificando formatação..."
	poetry run black --check src/
	poetry run isort --check-only src/

# 🏗️  Build
build: ## Build da aplicação
	@echo "🏗️  Fazendo build da aplicação..."
	poetry build

# 🐳 Docker
docker-build: ## Build da imagem Docker
	@echo "🐳 Construindo imagem Docker..."
	docker build -t solview-demo-app:latest .

docker-run: ## Executar container Docker
	@echo "🐳 Executando container Docker..."
	docker run -d \
		--name solview-demo-app \
		-p 8000:8000 \
		-e SOLVIEW_ENVIRONMENT=docker \
		solview-demo-app:latest

docker-stop: ## Parar container Docker
	@echo "🐳 Parando container Docker..."
	docker stop solview-demo-app || true
	docker rm solview-demo-app || true

docker-clean: ## Limpar imagens Docker
	@echo "🐳 Limpando imagens Docker..."
	docker rmi solview-demo-app:latest || true

# 🧹 Cleanup
clean: ## Limpar arquivos temporários
	@echo "🧹 Limpando arquivos temporários..."
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf .coverage htmlcov/ .pytest_cache/ .mypy_cache/

# 🚀 Production
production-check: ## Verificar se está pronto para produção
	@echo "🚀 Verificando se está pronto para produção..."
	$(MAKE) format-check
	$(MAKE) lint
	$(MAKE) test
	@echo "✅ Aplicação pronta para produção!"

# 📊 Observability
metrics-check: ## Verificar métricas
	@echo "📊 Verificando endpoint de métricas..."
	curl -f http://localhost:8000/metrics || echo "❌ Métricas não disponíveis"

health-check: ## Verificar health da aplicação
	@echo "❤️  Verificando health da aplicação..."
	curl -f http://localhost:8000/health || echo "❌ Health check falhou"

traces-test: ## Gerar traces para teste
	@echo "🔍 Gerando traces para teste..."
	for i in {1..10}; do \
		curl -s http://localhost:8000/api/catalog/products > /dev/null; \
		curl -s http://localhost:8000/api/cart/create > /dev/null; \
		sleep 1; \
	done
	@echo "✅ Traces gerados!"

# 🔧 Development Utils
requirements: ## Gerar requirements.txt
	@echo "📋 Gerando requirements.txt..."
	poetry export -f requirements.txt --output requirements.txt --without-hashes

tree: ## Mostrar estrutura do projeto
	@echo "🌳 Estrutura do projeto:"
	tree -I '__pycache__|*.pyc|.git|.pytest_cache|.mypy_cache|htmlcov' --dirsfirst

# 📈 Load Testing
load-test: ## Executar teste de carga simples
	@echo "📈 Executando teste de carga..."
	@for i in {1..100}; do \
		curl -s http://localhost:8000/api/catalog/products > /dev/null & \
	done; \
	wait
	@echo "✅ Teste de carga concluído!"

# 🔄 Development Workflow
dev-setup: install format test ## Setup completo para desenvolvimento
	@echo "✅ Setup de desenvolvimento concluído!"

ci-check: format-check lint test ## Verificação para CI/CD
	@echo "✅ Verificação de CI/CD concluída!"

# Default target
.DEFAULT_GOAL := help
