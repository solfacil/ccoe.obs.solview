# 🔒 Solview Data Masking

**Mascaramento de Dados Sensíveis com Solview (engine avançado)**

Este módulo fornece um engine avançado e extensível para mascarar informações sensíveis (CPF, CNPJ, telefone, e‑mail, tokens, JWT, cartões de crédito, etc.) antes de enviá-las para logs.

---

## ✨ Benefícios

- Fácil de aplicar no código (helpers `mask_sensitive_data`, `mask_dict`)
- Regras prontas: CPF/CNPJ/telefone/e‑mail, tokens (Bearer/Basic), JWT, cartões, senhas
- Engine extensível via `MaskingRule` e `EnhancedDataMasking`
- Validação de compliance (LGPD/GDPR/PCI) opcional

---

## 🚀 Como Habilitar e Usar

### 0. Habilitar por configuração (opcional)

```env
# .env — desabilita masking (útil para debug local)
IGNORE_MASK=true
```

```python
from solview import SolviewSettings

settings = SolviewSettings(ignore_mask=False)  # masking ativo (padrão)
```

> Observação: o masking é ativo por padrão. Use `ignore_mask=True` (ou `IGNORE_MASK=true`) para desabilitá-lo em ambientes de desenvolvimento. Também é possível desabilitar por chamada de log individual: `logger.info("texto", ignore_mask=True)`.

### 1. Mascarando uma String

```python
from solview.security import mask_sensitive_data
from solview import get_logger
logger = get_logger(__name__)

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
from solview.security import mask_dict
from solview import get_logger
logger = get_logger(__name__)

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
from solview.security import mask_dict
from solview import get_logger
logger = get_logger(__name__)

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
from solview.security import mask_dict
from solview import get_logger
logger = get_logger(__name__)

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

## 🔒 Masking e LGPD

O uso do `masking` em logs ajuda sua aplicação a cumprir requisitos da LGPD/GDPR, evitando exposição de dados pessoais sensíveis.

---

## 🧩 Engine Avançado (regras customizadas)

```python
from solview.security import EnhancedDataMasking, MaskingRule, enhanced_masking

# Adicionar nova regra (ex.: ID de contrato numérico de 10 dígitos)
enhanced_masking.add_rule(MaskingRule(
    name="contract_id",
    pattern=r"\b(\d{3})\d{4}(\d{3})\b",
    replacement=r"\1****\2",
    description="Contract ID masking"
))

texto = "contract_id=1234567890"
print(enhanced_masking.mask_text(texto))  # 123****890
```

### Validação de compliance (opcional)
```python
result = enhanced_masking.validate_compliance(
    text="CPF: 12345678909",
    compliance_standards=["LGPD"]
)
print(result)  # {"LGPD": False}
```

---

## 📝 Resumo

- Use `mask_sensitive_data()`/`mask_dict()` de `solview.security`.
- Use `IGNORE_MASK=true` para desabilitar masking em desenvolvimento.
- Aplique masking antes de enviar dados sensíveis para logs.
- Customize regras via `EnhancedDataMasking` quando necessário.

---

## 📚 Referências

- [Documentação Completa Solview](https://github.com/Solfacil/solview)
- Funções disponíveis: `mask_sensitive_data`, `mask_dict`, `enhanced_masking` (`solview.security`)

---

Dúvidas? Abra uma issue ou envie PR! ☀️