# 📚 Documentação Solview

Bem-vindo à documentação completa do **Solview** - a biblioteca de observabilidade de classe empresarial da Solfacil.

---

## 🎯 Guias Principais

### 🚀 **Começando**
- [📋 **Guia de Instrumentação**](instrumentation-guide.md) - Como instrumentar sua aplicação (⭐ **Essencial**)
- [🚀 **Guia de Deployment**](deployment-guide.md) - Deploy em desenvolvimento, staging e produção
- [🏗️ **Arquitetura e Componentes**](architecture.md) - Visão técnica detalhada

### ⚙️ **Configuração**
- [⚙️ **Configurações Universais**](universal-configuration-guide.md) - Todas as opções de configuração
 
- [☸️ **Deploy com Helm**](helm-deployment.md) - Kubernetes e Helm charts

### 📊 **Observabilidade**
- [📈 **Métricas**](metrics.md) - Métricas automáticas e customizadas
- [📝 **Logging**](logging.md) - Logs estruturados e correlação
- [🔍 **Tracing**](tracing.md) - Traces distribuídos e instrumentação
- [🗺️ **Service Graph**](service-graph-explanation.md) - Visualização da topologia
- [🤖 **MCP (FastMCP)**](mcp.md) - Observabilidade para servidores MCP

### 🎛️ **Grafana e Dashboards**
- [🔗 **Correlação no Grafana**](grafana-correlation-setup.md) - Setup de correlações automáticas
- [📊 **Dashboards**](dashboards.md) - Dashboards prontos e customização
- [🔍 **Correlação de Dados**](trace-correlation-guide.md) - Como funciona a correlação

### 🏢 **Uso Empresarial**
- [🔒 **Masking de Dados**](masking.md) - Proteção de dados sensíveis
- [🔄 **Migração v2**](migration-v2.md) - Guia de migração de versões
- [🧪 **Testes e Validação**](testing.md) - Como testar instrumentação
- [📊 **Best Practices**](best-practices.md) - Práticas recomendadas

---

## 🎯 Guias por Caso de Uso

### 👨‍💻 **Para Desenvolvedores**

**"Quero instrumentar minha API FastAPI"**
1. [📋 Guia de Instrumentação](instrumentation-guide.md) - Setup básico em 5 minutos
2. [📈 Métricas](metrics.md) - Métricas customizadas
3. [🔍 Tracing](tracing.md) - Traces manuais e automáticos

**"Quero instrumentar meu servidor MCP (FastMCP)"**
1. [🤖 Guia MCP](mcp.md) - Setup completo para FastMCP v2+
2. [📈 Métricas](metrics.md) - Métricas (reusa business_operations_*)
3. [🔍 Tracing](tracing.md) - Traces distribuídos

**"Quero testar localmente"**
1. [🚀 Quick Start](../README.md#-quick-start) - Docker Compose stack
2. [🧪 Testes](testing.md) - Validação da instrumentação

### 🛠️ **Para SREs/DevOps**

**"Quero fazer deploy em produção"**
1. [🚀 Guia de Deployment](deployment-guide.md) - Ambientes e configurações
2. [☸️ Deploy com Helm](helm-deployment.md) - Kubernetes
3. [🔒 Masking](masking.md) - Proteção de dados sensíveis

**"Quero configurar dashboards"**
1. [🔗 Correlação no Grafana](grafana-correlation-setup.md) - Setup automático
2. [📊 Dashboards](dashboards.md) - Dashboards prontos
3. [🗺️ Service Graph](service-graph-explanation.md) - Topologia de serviços

### 🏢 **Para Arquitetos**

**"Quero entender a arquitetura"**
1. [🏗️ Arquitetura](architecture.md) - Componentes e fluxos
2. [⚙️ Configurações](universal-configuration-guide.md) - Todas as opções
3. [📊 Best Practices](best-practices.md) - Práticas recomendadas

**"Quero garantir compliance"**
1. [🔒 Masking](masking.md) - Proteção de dados sensíveis
2. [🔄 Migração](migration-v2.md) - Estratégias de atualização

---

## 📚 Documentação Técnica

### 📊 **Componentes de Observabilidade**

| Componente | Função | Documentação |
|-----------|---------|--------------|
| **Métricas** | Prometheus metrics com correlação | [📈 Metrics Guide](metrics.md) |
| **Logs** | Structured logging com JSON | [📝 Logging Guide](logging.md) |
| **Traces** | OpenTelemetry distributed tracing | [🔍 Tracing Guide](tracing.md) |
| **Correlação** | Automatic trace ↔ metrics ↔ logs | [🔗 Correlation Guide](trace-correlation-guide.md) |
| **MCP** | Observabilidade para servidores FastMCP | [🤖 MCP Guide](mcp.md) |

### 🎛️ **Stack de Visualização**

| Ferramenta | Função | Configuração |
|-----------|---------|--------------|
| **Grafana** | Dashboards e correlação | [🔗 Grafana Setup](grafana-correlation-setup.md) |
| **Prometheus** | Métricas e alerting | [📈 Metrics Config](metrics.md) |
| **Loki** | Log aggregation | [📝 Logging Config](logging.md) |
| **Tempo** | Trace storage e service graph | [🗺️ Service Graph](service-graph-explanation.md) |

---

## 🎓 Tutoriais e Exemplos

### 🚀 **Quick Start (5 minutos)**

```python
from fastapi import FastAPI
from solview import SolviewSettings, setup_logger, setup_tracer
from solview.metrics import SolviewPrometheusMiddleware, prometheus_metrics_response

# 1. Configuração
settings = SolviewSettings(service_name="minha-api")
app = FastAPI()

# 2. Setup Solview
setup_logger(settings)
setup_tracer(settings, app)
app.add_middleware(SolviewPrometheusMiddleware, settings=settings)
app.add_route("/metrics", prometheus_metrics_response)

# 3. Sua API instrumentada automaticamente!
@app.get("/")
async def root():
    return {"message": "API com observabilidade completa!"}
```

### 🎯 **Casos de Uso Comuns**

- [🔄 **Microserviços**](examples/microservices.md) - Instrumentação de múltiplos serviços
- [🛒 **E-commerce API**](examples/ecommerce.md) - Exemplo completo com business metrics
- [🏦 **API Financeira**](examples/fintech.md) - Compliance e masking de dados
- [📱 **Mobile Backend**](examples/mobile-api.md) - Otimizações para mobile

---

## 🔧 Configuração por Ambiente

### 🏠 **Desenvolvimento**
```bash
ENVIRONMENT=dev
LOG_LEVEL=DEBUG
ENABLE_MEMORY_PROFILING=true
SAMPLING_MEMORY_PROFILING=1.0
```

### 🧪 **Staging**
```bash
ENVIRONMENT=stg
LOG_LEVEL=INFO
ENABLE_MEMORY_PROFILING=true
SAMPLING_MEMORY_PROFILING=0.1
```

### 🚀 **Produção**
```bash
ENVIRONMENT=prd
LOG_LEVEL=INFO
ENABLE_MEMORY_PROFILING=true
SAMPLING_MEMORY_PROFILING=0.01
```

> **Nota:** `trace_sampling_ratio` é configurado programaticamente via `TracingSettings(trace_sampling_ratio=0.05)`.

---

## 🛠️ Ferramentas e Scripts

### 📊 **Scripts de Observabilidade**
- `scripts/start-demo.sh` - Iniciar demo completa
- `scripts/quick-test.sh` - Teste rápido de funcionamento
- `scripts/generate-observability.sh` - Gerador de carga para testes
- `scripts/production-readiness-check.py` - Validação para produção
- `scripts/security-audit.py` - Auditoria de segurança

### 🔍 **Validação**
```bash
# Verificar instrumentação
curl http://localhost:8000/metrics | grep http_requests_total

# Testar correlação
# Acessar Grafana -> Explore -> Tempo -> Trace -> "Request Rate"

# Validar logs estruturados
# Logs devem estar em JSON com trace_id
```

---

## ❓ FAQ e Troubleshooting

### 🔧 **Problemas Comuns**

**P: Métricas não aparecem no Prometheus**
```bash
# Verificar endpoint
curl http://localhost:8000/metrics

# Verificar configuração Prometheus
docker logs solview-prometheus
```

**P: Traces não aparecem no Grafana**
```bash
# Verificar OTLP endpoint
curl http://localhost:4317/v1/traces

# Verificar variáveis de ambiente
env | grep OTLP_EXPORTER
```

**P: Correlação não funciona**
- Verificar configuração do datasource no Grafana
- Verificar se traces têm service.name correto
- Verificar se métricas têm labels service_name

---

## 🤝 Contribuição e Suporte

### 📞 **Suporte Técnico**
- **Email**: ccoe@solfacil.com.br
- **Teams**: Canal #observabilidade
- **Wiki**: [Confluence Observability](https://solfacil.atlassian.net)

### 🛠️ **Contribuir**
- **GitHub Issues**: Para bugs e features
- **Pull Requests**: Siga as guidelines
- **Documentação**: Sempre atualizar junto com código

### 🎓 **Treinamentos**
- **Workshop Interno**: Instrumentação com Solview
- **Brown Bag**: Observabilidade na prática
- **Tech Talk**: Casos de uso avançados

---

## 🗺️ Roadmap

### 🚀 **v2.1 (Q1 2024)**
- [ ] Instrumentação automática para Django
- [ ] Suporte a Azure Monitor
- [ ] Dashboards para business metrics

### 🌟 **v2.2 (Q2 2024)**
- [ ] AI-powered anomaly detection
- [ ] Auto-scaling baseado em métricas
- [ ] Multi-tenant observability

---

<div align="center">

**📚 Documentação completa para observabilidade de classe empresarial**

[🏠 Home](../README.md) | [🚀 Quick Start](../README.md#-quick-start) | [📋 Instrumentação](instrumentation-guide.md)

---

### 🎯 **Próximos Passos Recomendados**

**Novo no Solview?** → [📋 Guia de Instrumentação](instrumentation-guide.md)  
**Deploy em produção?** → [🚀 Guia de Deployment](deployment-guide.md)  
**Configurar dashboards?** → [🔗 Correlação no Grafana](grafana-correlation-setup.md)  
**Questões de masking?** → [🔒 Masking](masking.md)

</div>
