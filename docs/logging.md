# 📑 Logging Estruturado com Solview

O módulo de **logging estruturado** do **Solview** padroniza logs em formato JSON seguindo o Elastic Common Schema (ECS), facilitando sua integração com ferramentas modernas como ELK, Grafana, Loki, DataDog, StackDriver e outras.

---

## 🚀 Configuração Inicial

Configure o logger no início da execução do seu aplicativo:

```python
from solview.settings import SolviewSettings
from solview.logging import setup_logger
from loguru import logger

# Carrega automaticamente de variáveis de ambiente ou arquivo .env
settings = SolviewSettings()
setup_logger(settings)

logger.info("API inicializada com sucesso", extra={"request_id": "abc-123"})
```

### 🛠️ Opções de Configuração

Configure variáveis de ambiente ou um arquivo `.env`:

```env
SOLVIEW_LOG_LEVEL=INFO
SOLVIEW_ENVIRONMENT=production
SOLVIEW_SERVICE_NAME=api-pedidos
SOLVIEW_DOMAIN=vendas
SOLVIEW_SUBDOMAIN=checkout
SOLVIEW_VERSION=2.0.0
```

---

## 🖥️ Ambientes de Execução

### Desenvolvimento

Logs aparecem em formato colorido e amigável no terminal:

```
2025-05-07 11:10:22.123 | INFO     | module:function:45 - API inicializada com sucesso
```

### Produção

Logs são enviados em formato JSON (ECS):

```json
{
  "@timestamp": "2025-05-07T11:10:22.123456Z",
  "message": "API inicializada com sucesso",
  "level": "info",
  "service": {
    "name": "api-pedidos",
    "environment": "production",
    "version": "2.0.0",
    "domain": "vendas",
    "subdomain": "checkout"
  },
  "log": {
    "logger": "module",
    "module": "module",
    "level": "info",
    "file": {"path": "/app/module.py"},
    "origin": {
      "file": {"line": 45, "name": "module.py"},
      "function": "function"
    }
  },
  "process": {
    "pid": 12345,
    "name": "MainProcess",
    "thread": {"id": 139837, "name": "MainThread"}
  },
  "labels": {"request_id": "abc-123"}
}
```

---

## 🔒 Máscara Automática de Dados Sensíveis

Para evitar exposição de dados sensíveis, utilize a função de mascaramento fornecida:

```python
from solview.common.masking import mask_sensitive_data
from loguru import logger

masked_message = mask_sensitive_data("CPF: 12345678909, email=usuario@email.com")
logger.info(masked_message)
```

Exemplo mascarado:

```
CPF: 123.XXX.XXX-09, email=usu***@email.com
```

---

## 🗂️ Integração com outros frameworks

### Exemplo com FastAPI

```python
from fastapi import FastAPI
from solview.settings import SolviewSettings
from solview.logging import setup_logger

app = FastAPI()
setup_logger(SolviewSettings(service_name="api-clientes"))
```

Agora todos os logs da aplicação estarão estruturados automaticamente.

---

## ⚙️ Personalização Avançada

É possível configurar parâmetros adicionais diretamente:

```python
from solview.logging.settings import LoggingSettings
from solview.logging import setup_logger

custom_settings = LoggingSettings(
    log_level="DEBUG",
    environment="staging",
    service_name="worker-pagamentos",
    domain="financeiro",
    subdomain="pagamentos",
    version="1.3.2"
)

setup_logger(custom_settings)
```

---

## 📈 Melhores práticas

* Utilize sempre `extra` para metadados adicionais (ex: `request_id`).
* Aproveite o mascaramento automático para garantir compliance.
* Monitore o volume e tamanho dos logs em produção.
* Configure dashboards específicos no ELK, Loki ou Grafana para aproveitar plenamente os logs estruturados.

---

Com isso, você terá um sistema robusto e padronizado de logging para melhorar sua observabilidade.
