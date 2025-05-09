# 🔒 Solview Data Masking

**Mascaramento de Dados Sensíveis com Solview**

Este módulo do Solview fornece funções utilitárias para mascarar informações sensíveis (CPF, CNPJ, telefone, e-mail) antes de enviá-las para logs, tornando sua aplicação mais segura e protegida contra vazamentos de dados pessoais, especialmente ao integrar com Loki, Grafana, ou ELK.

---

## ✨ Benefícios

- Fácil de aplicar no código
- Suporte a formatos brasileiros de CPF, CNPJ, telefone e e-mail
- Pode mascarar strings isoladas ou dicionários inteiros recursivamente

---

## 🚀 Como Usar

### 1. Mascarando uma String

```python
from solview.common.masking import mask_sensitive_data
from loguru import logger

texto = "CPF: 12345678909, email: joao@email.com, tel: 11987654321"
logger.info(mask_sensitive_data(texto))
```

**Saída no log:**
```
CPF: 123.XXX.XXX-09, email: joa***@email.com, tel: 11*****4321
```

---

### 2. Mascarando um Dicionário Recursivamente

```python
from solview.common.masking import mask_dict
from loguru import logger

payload = {
    "cpf": "12345678909",
    "email": "joao@email.com",
    "dados": {"telefone": "11987654321", "cnpj": "12345678000199"}
}
logger.info(mask_dict(payload))
```

**Saída mascarada:**
```json
{
  "cpf": "123.XXX.XXX-09",
  "email": "joa***@email.com",
  "dados": {
    "telefone": "11*****4321",
    "cnpj": "12.XXX.XXX/XXXX-99"
  }
}
```

---

## 🤖 Uso no FastAPI

Aplique o mascaramento diretamente ao logar informações sensíveis:

```python
from fastapi import FastAPI, Request
from solview.common.masking import mask_dict
from loguru import logger

app = FastAPI()

@app.post("/usuario")
async def criar_usuario(request: Request):
    dados = await request.json()
    logger.info(mask_dict(dados))
    return {"msg": "Usuário criado (dados mascarados no log)"}
```

---

## ⚙️ Automação Avançada: Middleware para Requests

Para quem deseja mascarar automaticamente o corpo dos requests:

```python
from fastapi import FastAPI, Request
from solview.common.masking import mask_dict
from loguru import logger

app = FastAPI()

@app.middleware("http")
async def log_masked_request(request: Request, call_next):
    try:
        if request.method in ['POST', 'PUT', 'PATCH']:
            body = await request.json()
            logger.info(f"Request recebido: {mask_dict(body)}")
    except Exception:
        pass  # Ignorar erros caso não seja JSON

    response = await call_next(request)
    return response
```

> **Atenção:** Automatizar o masking de todos os requests pode mascarar campos desnecessários ou afetar debugging. Prefira aplicar explicitamente apenas nas informações sensíveis.

---

## 🛡️ Segurança e LGPD

O uso do `masking` em logs ajuda sua aplicação a cumprir requisitos da LGPD/GDPR, evitando exposição de dados pessoais sensíveis.

---

## 📝 Resumo

- Use `mask_sensitive_data()` para strings com dados sensíveis.
- Use `mask_dict()` para dicionários, inclusive aninhados.
- Aplique antes de enviar qualquer dado sensível para o logger.
- O masking não é aplicado automaticamente em todas as mensagens — você escolhe onde aplicar!

---

## 📚 Referências

- [Documentação Completa Solview](https://github.com/Solfacil/solview)
- Funções disponíveis: `mask_sensitive_data`, `mask_dict` (`solview.common.masking`)

---

Dúvidas? Abra uma issue ou envie PR! ☀️