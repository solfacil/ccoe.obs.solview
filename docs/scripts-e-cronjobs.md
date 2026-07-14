# 📋 Scripts e Cronjobs com Solview

Scripts de curta duração e cronjobs Kubernetes não podem servir um endpoint HTTP persistente — o processo termina antes do Prometheus conseguir fazer scrape. Para esses casos, o Solview usa o **modelo push via Prometheus Pushgateway**:

```
Script → push_metrics_to_gateway() → Pushgateway ← scrape ← Prometheus
```

O processo termina normalmente. O Pushgateway guarda as métricas até o próximo scrape.

---

## 🚀 Uso Rápido: Decorator

O decorator `script_job_instrumentation` é a forma mais simples de instrumentar scripts. Funciona com funções **síncronas e assíncronas**.

### Script Síncrono

```python
from solview import setup_settings, setup_logger, script_job_instrumentation
from solview.settings import SolviewSettings

setup_settings(SolviewSettings(service_name="exportador-relatorios"))
setup_logger()


@script_job_instrumentation(
    "exportacao-diaria",
    gateway_url="http://pushgateway:9091",
)
def exportar_relatorios():
    # lógica do script
    registros = buscar_registros_do_dia()
    salvar_csv(registros)


if __name__ == "__main__":
    exportar_relatorios()
    # ↑ ao terminar, as métricas são enviadas automaticamente ao Pushgateway
```

### Script Assíncrono

```python
import asyncio
from solview import setup_settings, setup_logger, script_job_instrumentation
from solview.settings import SolviewSettings

setup_settings(SolviewSettings(service_name="sync-faturas"))
setup_logger()


@script_job_instrumentation(
    "sync-faturas",
    gateway_url="http://pushgateway:9091",
)
async def sincronizar_faturas():
    async for fatura in repo.listar_pendentes():
        await processar(fatura)


if __name__ == "__main__":
    asyncio.run(sincronizar_faturas())
```

### Com instâncias paralelas (grouping_key)

Se o mesmo cronjob roda em múltiplos pods ao mesmo tempo, use `grouping_key` para diferenciar as instâncias. Sem isso, os pods sobrescrevem as métricas uns dos outros no Pushgateway.

```python
import socket
from solview import script_job_instrumentation

@script_job_instrumentation(
    "importacao-clientes",
    gateway_url="http://pushgateway:9091",
    grouping_key={"instance": socket.gethostname()},
)
def importar_clientes():
    ...
```

---

## 🔧 Uso Manual: Context Manager

Para scripts onde o decorator não se encaixa, use `script_metrics_context`:

```python
from solview.metrics import script_metrics_context
from solview.metrics.custom import SCRIPT_RUNS_TOTAL

with script_metrics_context("http://pushgateway:9091", "meu-script"):
    # registre métricas manualmente dentro do bloco
    try:
        processar()
        SCRIPT_RUNS_TOTAL.labels(
            job_name="meu-script",
            app_name="meu-servico",
            status="success",
        ).inc()
    except Exception:
        SCRIPT_RUNS_TOTAL.labels(
            job_name="meu-script",
            app_name="meu-servico",
            status="error",
        ).inc()
        raise
# push ocorre aqui, mesmo que uma exceção tenha sido levantada
```

### Limpeza após execução (`delete_on_exit`)

Se cada execução do script deve ser tratada de forma isolada e você não quer que métricas de uma execução anterior apareçam no Prometheus entre os runs:

```python
with script_metrics_context(
    "http://pushgateway:9091",
    "job-isolado",
    delete_on_exit=True,  # remove as métricas do Pushgateway após o push
):
    executar_job()
```

### Push e delete manuais

```python
from solview.metrics import push_metrics_to_gateway, delete_metrics_from_gateway

# Enviar métricas
sucesso = push_metrics_to_gateway(
    gateway_url="http://pushgateway:9091",
    job_name="meu-script",
    grouping_key={"instance": "pod-1"},
)

# Remover métricas (cleanup)
delete_metrics_from_gateway(
    gateway_url="http://pushgateway:9091",
    job_name="meu-script",
)
```

> **Nota:** `push_metrics_to_gateway` nunca levanta exceções — falhas de rede são logadas como `WARNING` e o script continua normalmente.

---

## 📊 Métricas Disponíveis

O decorator registra automaticamente as seguintes métricas:

| Métrica | Tipo | Labels | Descrição |
|---|---|---|---|
| `script_runs_total` | Counter | `job_name`, `app_name`, `status` | Total de execuções por status (`success`/`error`) |
| `script_duration_seconds` | Histogram | `job_name`, `app_name`, `status` | Duração total da execução em segundos |
| `script_last_success_timestamp` | Gauge | `job_name`, `app_name` | Unix timestamp da última execução bem-sucedida |
| `script_last_run_timestamp` | Gauge | `job_name`, `app_name` | Unix timestamp da última execução (qualquer resultado) |
| `script_memory_samples_total` | Counter | `job_name`, `app_name` | Amostras de memória coletadas (quando profiling ativo) |
| `script_memory_bytes` | Histogram | `job_name`, `app_name`, `status` | Uso de memória por execução |

---

## 🔔 Alertas Recomendados

### Job parado (sem execução por mais tempo que o esperado)

```promql
# Alerta se o script não rodou com sucesso nas últimas 2 horas
time() - script_last_success_timestamp{job_name="exportacao-diaria"} > 7200
```

```promql
# Alerta se o script não iniciou nas últimas 2 horas
time() - script_last_run_timestamp{job_name="exportacao-diaria"} > 7200
```

### Taxa de erros alta

```promql
# Alerta se mais de 3 execuções falharam na última hora
increase(script_runs_total{job_name="sync-faturas", status="error"}[1h]) > 3
```

### Duração anormal

```promql
# Alerta se o job demorou mais de 30 minutos na última execução
script_duration_seconds{job_name="importacao-clientes", status="success"} > 1800
```

---

## ⚙️ Configuração do Pushgateway

### docker-compose.yml

Adicione o Pushgateway à stack local:

```yaml
services:
  pushgateway:
    image: prom/pushgateway:v1.10.0
    ports:
      - "9091:9091"
    restart: unless-stopped
```

### prometheus.yml — scrape config

Configure o Prometheus para fazer scrape do Pushgateway:

```yaml
scrape_configs:
  - job_name: pushgateway
    honor_labels: true  # preserva os labels enviados pelos scripts
    static_configs:
      - targets: ["pushgateway:9091"]
    scrape_interval: 30s
```

> **`honor_labels: true`** é obrigatório. Sem ele, o Prometheus sobrescreve o label `job` com o nome do job de scrape (`pushgateway`), perdendo o nome original do script.

---

## ✅ Boas Práticas

### Convenção de nomes para `job_name`

Use kebab-case com contexto de negócio. Evite nomes genéricos como `script` ou `job`.

```
# Bom
"exportacao-faturas-mensais"
"sync-clientes-crm"
"limpeza-sessoes-expiradas"

# Ruim
"script"
"job1"
"cronjob"
```

### Usar `gateway_url` via variável de ambiente

Não hardcode a URL do Pushgateway no código:

```python
import os
from solview import script_job_instrumentation

GATEWAY_URL = os.getenv("PUSHGATEWAY_URL", "http://pushgateway:9091")

@script_job_instrumentation("meu-job", gateway_url=GATEWAY_URL)
def meu_job():
    ...
```

### Profiling de memória

Ative para scripts que processam grandes volumes de dados:

```python
from solview import setup_settings
from solview.settings import SolviewSettings

setup_settings(SolviewSettings(
    service_name="importador-dados",
    enable_memory_profiling=True,
    sampling_memory_profiling=1.0,  # 100% em desenvolvimento
))
```

Em produção, use `sampling_memory_profiling=0.1` (10%) para reduzir overhead.

---

## 🔍 Troubleshooting

**Métricas não aparecem no Prometheus**

1. Verifique se o Pushgateway está acessível: `curl http://pushgateway:9091/metrics`
2. Verifique se o Prometheus tem o scrape configurado com `honor_labels: true`
3. Verifique os logs do script — se o push falhou, haverá um `WARNING` com o motivo

**Métricas de execuções antigas aparecem entre os runs**

Isso é comportamento esperado do Pushgateway (ele guarda o último estado). Se quiser limpar entre runs, use `delete_on_exit=True` no `script_metrics_context` ou passe `delete_on_exit=True` nos parâmetros.

**Script crasha ao tentar enviar métricas**

`push_metrics_to_gateway` não levanta exceções. Se o script está crashando durante o push, verifique se a chamada está sendo feita fora do Solview (via `prometheus_client` diretamente).

**Múltiplos pods sobrescrevendo métricas**

Use `grouping_key={"instance": socket.gethostname()}` para isolar cada instância. Veja a seção [Com instâncias paralelas](#com-instâncias-paralelas-grouping_key) acima.
