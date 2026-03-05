# 📋 Changelog

Todas as mudanças notáveis do **Solview** serão documentadas neste arquivo.

O formato é baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.0.0/), e este projeto adere ao [Versionamento Semântico](https://semver.org/lang/pt-BR/).

---

## [3.0.0] - 2026-03-04

### ✨ Adicionado
- **Módulo `solview.mcp`** para observabilidade de servidores FastMCP (v2+)
- **`SolviewMCPMiddleware`** — middleware FastMCP que instrumenta tool calls, resource reads e prompt gets com spans OpenTelemetry e métricas Prometheus (`business_operations_*`)
- **`setup_tracer()` unificado** — aceita `app=None`; quando sem app (FastMCP/scripts), aplica apenas auto-instrumentações de biblioteca; quando com FastAPI, aplica também FastAPIInstrumentor e prometheus-fastapi-instrumentator
- **Dependência opcional** `solview[mcp]` via `pip install solview[mcp]`
- **Testes completos** em `tests/mcp/` (middleware, memory profiling, tracing, setup)
- **Documentação** `docs/mcp.md` com guia completo de uso
- `opentelemetry-instrumentation-redis` — auto-instrumentação para `redis` (sync) e `redis.asyncio` (async)
- `RedisInstrumentor().instrument()` em `setup_tracer()` (FastAPI e MCP)
- Decorator `redis_client_instrumentation(command="get")` para instrumentação manual com métricas Prometheus
- Métricas Redis: `redis_operations_total`, `redis_operations_duration_seconds`, `redis_operations_errors_total`, `redis_operations_memory_bytes`, `redis_operations_memory_samples_total` (labels: `command`, `app_name`, `status`, `error_type`)

---

## [2.0.1] - 2025-08-20

### ✨ Adicionado
- **Correlação automática** trace-to-metrics no Grafana com sintaxe corrigida
- **Service Graph** automático via Tempo metrics generator
- **Masking automático** de dados sensíveis (LGPD/GDPR compliance)
- **Instrumentação zero-code** para FastAPI com middlewares
- **Métricas padronizadas** compatíveis com OpenTelemetry
- **Logs estruturados** em JSON com correlação automática
- **Scripts de observabilidade** para testes e validação
- **Documentação completa** para uso empresarial

### 🔧 Modificado
- **Métricas renomeadas** para padrão universal (`http_requests_total`, `http_responses_total`)
- **Configuração simplificada** via variáveis de ambiente
- **Performance otimizada** com batching e sampling configurável
- **Segurança aprimorada** com middleware de validação

### 🐛 Corrigido
- **Interpolação de traces** no Grafana usando sintaxe `${__span.tags["service.name"]}`
- **Correlação automática** funcionando entre traces, logs e métricas
- **Service Graph** aparecendo corretamente no Grafana
- **Propagação de contexto** entre microsserviços
- **Masking de PII** em logs e traces

### 🔒 Segurança
- **Data masking** automático para campos sensíveis
- **Validação de entrada** em todos os endpoints
- **Headers de segurança** configuráveis
- **Auditoria de acesso** com logs estruturados

---

## [2.0.0] - 2025-08-15

### ✨ Adicionado
- **Reescrita completa** da biblioteca para Python 3.11+
- **Suporte nativo** ao OpenTelemetry
- **Integração total** com stack LGTM (Loki, Grafana, Tempo, Mimir)
- **Auto-instrumentação** para FastAPI, SQLAlchemy, HTTPX
- **Configuração unificada** via Pydantic Settings

### 💥 Breaking Changes
- **API completamente nova** - migração necessária da v1.x
- **Dependências atualizadas** - Python 3.11+ obrigatório
- **Configuração modificada** - variáveis de ambiente padronizadas

---

## [1.2.3] - 2023-12-10

### 🐛 Corrigido
- Bug crítico em logging assíncrono
- Vazamento de memória em traces de longa duração
- Compatibilidade com FastAPI 0.104+

---

## [1.2.0] - 2023-11-15

### ✨ Adicionado
- Suporte inicial ao OpenTelemetry
- Métricas customizadas via Prometheus
- Logs estruturados com Loguru

### 🔧 Modificado
- Performance melhorada em 40%
- Redução de overhead de instrumentação

---

## [1.1.0] - 2023-10-01

### ✨ Adicionado
- Instrumentação automática para FastAPI
- Dashboard básico do Grafana
- Alertas do Prometheus

---

## [1.0.0] - 2025-06-01

### ✨ Primeira versão
- **Logging básico** estruturado
- **Métricas** HTTP simples  
- **Tracing** manual com Jaeger
- **Documentação** inicial

---

## 🤝 Contribuidores

### 👥 **Core Team**
- **Jefferson Martins** - Arquiteto Principal (@jmartins)
- **CCOE Team** - Centro de Excelência em Observabilidade
- **SRE Team** - Reliability Engineering

### 🎯 **Agradecimentos Especiais**
- **ChatGPT 5.0** - Solução da interpolação de traces no Grafana
- **OpenTelemetry Community** - Especificações e SDKs
- **Grafana Labs** - Stack LGTM e documentação
- **Solfacil Engineering** - Feedback e casos de uso

---

## 📞 Suporte e Contato

### 🏢 **Suporte Interno (Solfacil)**
- **Email**: ccoe@solfacil.com.br
- **Teams**: Canal #observabilidade
- **Confluence**: [Solview Wiki](https://solfacil.atlassian.net)
- **Jira**: Projeto CCOE para issues e features

### 🌐 **Comunidade**
- **GitHub Issues**: Para bugs e feature requests
- **GitHub Discussions**: Para dúvidas e ideias
- **Internal Wiki**: Documentação colaborativa
- **Brown Bags**: Sessões semanais de Q&A

### 📚 **Documentação**
- **Docs**: [Documentação completa](docs/README.md)

---

<div align="center">

**📋 Acompanhe a evolução do Solview**

[🏠 Home](README.md) | [📚 Docs](docs/README.md) | [🚀 Quick Start](README.md#-quick-start)

---

*Mantido com ❤️ pela equipe de **Centro de Excelência em Observabilidade** da Solfacil*

</div>
