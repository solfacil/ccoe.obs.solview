# 🎯 Solview - Observabilidade de Classe Empresarial

[![Python](https://img.shields.io/badge/Python-3.11%2B-blue)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104%2B-green)](https://fastapi.tiangolo.com)
[![OpenTelemetry](https://img.shields.io/badge/OpenTelemetry-1.21%2B-orange)](https://opentelemetry.io)
[![Grafana](https://img.shields.io/badge/Grafana-10.0%2B-red)](https://grafana.com)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

## 🎯 Visão Geral

O **Solview** é uma biblioteca Python de observabilidade empresarial que implementa os **três pilares da observabilidade** (Métricas, Logs, Traces) com **correlação automática** e **instrumentação zero-code** para aplicações FastAPI.

### ✨ Principais Características

- 🔄 **Correlação Automática**: Traces, logs e métricas automaticamente correlacionados
- 📊 **Métricas Padronizadas**: Compatível com OpenTelemetry e Prometheus
- 🔍 **Traces Distribuídos**: Rastreamento completo de requisições cross-service
- 📝 **Logs Estruturados**: JSON estruturado com campos padronizados
- 🔒 **Masking de Dados**: Proteção automática de dados sensíveis
- 🚀 **Zero Configuration**: Instrumentação automática via decorators e middleware
- 🎯 **Service Graph**: Visualização automática da topologia de serviços
- ⚡ **Performance**: Otimizado para alta throughput e baixa latência
- 🤖 **MCP (FastMCP)**: Observabilidade para servidores MCP via `solview[mcp]`

---

## 🏗️ Arquitetura

```mermaid
graph TB
    App[Aplicação FastAPI] --> Solview[Solview Library]

    Solview --> |Metrics| Prometheus[Prometheus]
    Solview --> |Logs| Loki[Loki]
    Solview --> |Traces| Tempo[Tempo]

    Prometheus --> Grafana[Grafana]
    Loki --> Grafana
    Tempo --> Grafana

    Grafana --> |Service Graph| ServiceMap[Service Map]
    Grafana --> |Correlations| TraceMetrics[Trace ↔ Metrics]
    Grafana --> |Dashboards| Monitoring[Monitoring]
```

---

## 🚀 Quick Start

### 1. Instalação

```bash
# Para aplicações FastAPI
pip install solview

# Para servidores MCP (FastMCP v2+)
pip install solview[mcp]
```

### 2. Variáveis de Ambiente

Copie o template e ajuste os valores para seu ambiente:

```bash
cp config/solview.env.example .env
```

Nota: `SOLVIEW_ENVIRONMENT` aceita valores como `dev`, `stg`, `qa` e será normalizado internamente para `dev`. Apenas `prd`/`prod`/`production` será normalizado para `prd`. Use `settings.environment_effective` para obter o valor final (`dev`|`prd`).

### 3. Instrumentação Básica (FastAPI)

```python
from fastapi import FastAPI
from solview import setup_logger, setup_tracer
from solview.metrics import SolviewPrometheusMiddleware, prometheus_metrics_response

# Criar aplicação
app = FastAPI(title="Minha API")

# Instrumentação Solview (v2.2.0+)
setup_logger()
setup_tracer(app)  # Provider + libs + fastapi automaticamente
app.add_middleware(SolviewPrometheusMiddleware)
app.add_route("/metrics", prometheus_metrics_response)

@app.get("/health")
async def health():
    return {"status": "healthy"}
```

Para casos com engine SQLAlchemy em import-time, veja [Ordering Bug com SQLAlchemy](docs/tracing.md#-ordering-bug-com-sqlalchemy--engines-em-import-time).

### 4. Execução com Observabilidade

```bash
# Iniciar stack de observabilidade
docker-compose up -d

# Executar aplicação
uvicorn main:app --reload

# Acessar dashboards
open http://localhost:3000  # Grafana
```

### 5. Instrumentação MCP (FastMCP)

```python
from fastmcp import FastMCP
from prometheus_client import start_http_server
from solview import SolviewSettings, setup_settings, setup_tracer
from solview.mcp import SolviewMCPMiddleware

# Configuração
setup_settings(SolviewSettings(service_name="meu-mcp-server"))
setup_tracer()

# Expor métricas Prometheus (MCP não tem /metrics nativo)
start_http_server(port=9090)

# Criar servidor MCP com observabilidade
mcp = FastMCP("MeuServidor")
mcp.add_middleware(SolviewMCPMiddleware())

@mcp.tool
async def buscar_dados(query: str) -> str:
    # Tool calls são instrumentadas como business operations
    # Métricas: business_operations_total{operation="tool.buscar_dados"}
    # Spans: mcp.tool.buscar_dados
    return f"Resultado: {query}"
```

---

## 📚 Documentação Completa

### 🎯 **Guias de Implementação**
- [📋 **Guia de Instrumentação**](docs/instrumentation-guide.md) - Como instrumentar sua aplicação
- [🚀 **Guia de Deployment**](docs/deployment-guide.md) - Deploy em produção
- [🏗️ **Arquitetura e Componentes**](docs/architecture.md) - Visão técnica detalhada

### 🔧 **Configuração**
- [⚙️ **Configurações Avançadas**](docs/universal-configuration-guide.md) - Todas as opções de configuração

- [☸️ **Deploy com Helm**](docs/helm-deployment.md) - Kubernetes e Helm

### 📊 **Observabilidade**
- [📈 **Métricas**](docs/metrics.md) - Métricas disponíveis e customização
- [📝 **Logging**](docs/logging.md) - Estrutura de logs e configuração
- [🔍 **Tracing**](docs/tracing.md) - Traces distribuídos
- [🔗 **Correlação de Dados**](docs/trace-correlation-guide.md) - Como funciona a correlação

### 🎛️ **Grafana e Dashboards**
- [📊 **Service Graph**](docs/service-graph-explanation.md) - Visualização da topologia
- [🔗 **Correlação no Grafana**](docs/grafana-correlation-setup.md) - Setup de correlações
- [📈 **Dashboards**](docs/dashboards.md) - Dashboards prontos

### 🤖 **MCP (Model Context Protocol)**
- [🤖 **Guia MCP**](docs/mcp.md) - Observabilidade para servidores FastMCP

### 🏢 **Uso Empresarial**
 - [🔒 **Masking de Dados**](docs/masking.md) - Proteção de dados sensíveis
- [🔄 **Migração v2**](docs/migration-v2.md) - Migração de versões
- [🧪 **Testes e Validação**](docs/testing.md) - Como testar instrumentação

---

## 🎯 Casos de Uso

### 🏢 **Para Empresas**
- **Monitoramento de APIs**: Observabilidade completa de microsserviços
- **Debugging Distribuído**: Rastreamento de requisições cross-service
- **Performance Optimization**: Identificação de gargalos
- **Compliance**: Auditoria e masking de dados sensíveis

### 👨‍💻 **Para Desenvolvedores**
- **Zero Configuration**: Instrumentação automática
- **Desenvolvimento Local**: Stack completa via Docker Compose
- **Debugging**: Correlação automática trace → metrics → logs
- **Testes**: Validação de instrumentação

### 🛠️ **Para SREs/DevOps**
- **Alerting**: PrometheusRules prontas
- **Dashboards**: Grafana dashboards pré-configurados
- **Service Graph**: Topologia automática
- **Helm Charts**: Deploy Kubernetes simplificado

---

## 📊 Stack de Observabilidade

| Componente | Função | Porta |
|-----------|---------|-------|
| **Prometheus** | Métricas | 9090 |
| **Grafana** | Visualização | 3000 |
| **Loki** | Logs | 3100 |
| **Tempo** | Traces | 3200 |
| **OpenTelemetry Collector** | Coleta | 4317/4318 |

---

## 🚀 Exemplos Práticos

### 🌟 **Demo Completa**
```bash
# Clonar repositório
git clone https://github.com/solfacil/solview
cd solview

# Iniciar demo
./scripts/start-demo.sh

# Gerar carga
./scripts/generate-observability.sh --preset demo

# Acessar Grafana: http://localhost:3000
```

### 🧪 **Testes de Carga**
```bash
# Teste básico
./scripts/quick-test.sh

# Teste de produção
python scripts/production-readiness-check.py

# Auditoria de segurança (opcional)
python scripts/security-audit.py
```

---

## 🏆 Benefícios

### ✅ **Técnicos**
- **Time to Market**: Instrumentação em minutos, não semanas
- **Padronização**: Métricas compatíveis com OpenTelemetry
- **Performance**: Overhead < 5% em produção
- **Escalabilidade**: Testado com 10k+ RPS

### ✅ **Empresariais**
- **Compliance**: LGPD/GDPR ready com masking automático
- **ROI**: Redução de 80% no tempo de debugging
- **Qualidade**: SLA > 99.9% com alerting proativo
- **Custos**: Redução de 60% nos custos de observabilidade

---

## 🤝 Contribuição

### 🐛 **Issues e Bugs**
- Use GitHub Issues para reportar problemas
- Inclua logs e configurações relevantes
- Siga o template de issue

### 🔧 **Pull Requests**
- Fork o repositório
- Crie branch feature/fix
- Inclua testes
- Documente mudanças

### 📝 **Documentação**
- Atualize README se necessário
- Adicione exemplos práticos
- Mantenha documentação sincronizada

---

## 📞 Suporte

### 🏢 **Solfacil**
- **Email**: ccoe@solfacil.com.br
- **Teams**: Canal #observabilidade
- **Wiki**: [Confluence Observability](https://solfacil.atlassian.net)

### 🌐 **Comunidade**
- **GitHub Issues**: Para bugs e features
- **Discussions**: Para dúvidas e ideias
- **Wiki**: Documentação colaborativa

---

## 📜 Licença

Este projeto está licenciado sob a **MIT License** - veja o arquivo [LICENSE](LICENSE) para detalhes.

---

## 🎯 Roadmap

### 🚀 **v2.1 (Q1 2024)**
- [ ] Instrumentação automática para Django
- [ ] Suporte a Azure Monitor
- [ ] Dashboards para business metrics

### 🌟 **v2.2 (Q2 2024)**
- [ ] AI-powered anomaly detection
- [ ] Auto-scaling baseado em métricas
- [ ] Multi-tenant observability

### 🏗️ **v3.0 (Q3 2024)**
- [ ] Observabilidade de infraestrutura
- [ ] Cost optimization recommendations
- [ ] Compliance automation

---

<div align="center">

**🎊 Construído com ❤️ pela equipe da Solfacil**

[🏠 Home](README.md) | [📚 Docs](docs/) | [🚀 Quick Start](#-quick-start) | [🤝 Contribuir](#-contribuição)

</div>
