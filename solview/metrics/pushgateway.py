"""
Push de métricas para o Prometheus Pushgateway.

Para scripts e cronjobs que não podem servir um endpoint HTTP persistente,
use push_metrics_to_gateway() para enviar as métricas acumuladas antes de sair.
O Prometheus então faz scrape do Pushgateway normalmente.

Fluxo:
  Script → push_metrics_to_gateway() → Pushgateway ← scrape ← Prometheus
"""

import logging
from contextlib import contextmanager
from typing import Optional

from prometheus_client import REGISTRY
from prometheus_client import push_to_gateway as _push_to_gateway
from prometheus_client import delete_from_gateway as _delete_from_gateway
from prometheus_client.exposition import default_handler

_logger = logging.getLogger("solview.metrics.pushgateway")


def push_metrics_to_gateway(
    gateway_url: str,
    job_name: str,
    grouping_key: Optional[dict] = None,
    timeout: int = 30,
    registry=REGISTRY,
) -> bool:
    """
    Envia as métricas do processo atual para o Prometheus Pushgateway.

    Falhas de rede são tratadas internamente (log WARNING) e nunca propagadas —
    o script não deve crashar por falha de observabilidade.

    Args:
        gateway_url: URL do Pushgateway, ex: "http://pushgateway:9091".
        job_name: Nome do job no Pushgateway. Deve ser único por tipo de script.
        grouping_key: Labels extras para identificar instâncias, ex: {"instance": "pod-abc"}.
        timeout: Timeout em segundos para a requisição HTTP.
        registry: Registry Prometheus a usar (padrão: REGISTRY global).

    Returns:
        True em caso de sucesso, False se o push falhou.

    Exemplo::

        from solview.metrics.pushgateway import push_metrics_to_gateway

        push_metrics_to_gateway(
            gateway_url="http://pushgateway:9091",
            job_name="exportacao-diaria",
            grouping_key={"instance": "cron-pod-abc123"},
        )
    """
    try:
        _push_to_gateway(
            gateway=gateway_url,
            job=job_name,
            registry=registry,
            grouping_key=grouping_key or {},
            handler=default_handler,
            timeout=timeout,
        )
        _logger.info(
            "Métricas enviadas ao Pushgateway",
            extra={"job_name": job_name, "gateway_url": gateway_url},
        )
        return True
    except Exception as exc:
        _logger.warning(
            "Falha ao enviar métricas ao Pushgateway — script continua normalmente",
            extra={
                "job_name": job_name,
                "gateway_url": gateway_url,
                "error": str(exc),
                "error_type": type(exc).__name__,
            },
        )
        return False


def delete_metrics_from_gateway(
    gateway_url: str,
    job_name: str,
    grouping_key: Optional[dict] = None,
    timeout: int = 30,
) -> bool:
    """
    Remove as métricas de um job do Prometheus Pushgateway.

    Útil para limpar métricas após um script finalizar, evitando que o Prometheus
    continue fazendo scrape de dados obsoletos entre execuções.

    Args:
        gateway_url: URL do Pushgateway.
        job_name: Nome do job a remover.
        grouping_key: Mesma grouping_key usada no push.
        timeout: Timeout em segundos para a requisição HTTP.

    Returns:
        True em caso de sucesso, False se falhou.

    Exemplo::

        from solview.metrics.pushgateway import delete_metrics_from_gateway

        delete_metrics_from_gateway(
            gateway_url="http://pushgateway:9091",
            job_name="exportacao-diaria",
        )
    """
    try:
        _delete_from_gateway(
            gateway=gateway_url,
            job=job_name,
            grouping_key=grouping_key or {},
            timeout=timeout,
        )
        _logger.info(
            "Métricas removidas do Pushgateway",
            extra={"job_name": job_name, "gateway_url": gateway_url},
        )
        return True
    except Exception as exc:
        _logger.warning(
            "Falha ao remover métricas do Pushgateway",
            extra={
                "job_name": job_name,
                "gateway_url": gateway_url,
                "error": str(exc),
                "error_type": type(exc).__name__,
            },
        )
        return False


@contextmanager
def script_metrics_context(
    gateway_url: str,
    job_name: str,
    grouping_key: Optional[dict] = None,
    timeout: int = 30,
    delete_on_exit: bool = False,
    registry=REGISTRY,
):
    """
    Context manager síncrono que faz push automático ao Pushgateway na saída.

    O push ocorre no bloco ``finally`` — mesmo que uma exceção seja levantada
    dentro do ``with``. A exceção não é suprimida.

    Args:
        gateway_url: URL do Pushgateway.
        job_name: Nome do job.
        grouping_key: Labels extras de instância.
        timeout: Timeout HTTP em segundos.
        delete_on_exit: Se True, apaga as métricas do gateway após o push.
            Útil quando cada execução é isolada e métricas antigas não devem
            persistir entre runs.
        registry: Registry Prometheus a usar.

    Exemplo::

        from solview.metrics.pushgateway import script_metrics_context

        with script_metrics_context("http://pushgateway:9091", "meu-script"):
            run_my_job()
        # push ocorre aqui, mesmo que run_my_job() tenha lançado exceção
    """
    try:
        yield
    finally:
        push_metrics_to_gateway(
            gateway_url=gateway_url,
            job_name=job_name,
            grouping_key=grouping_key,
            timeout=timeout,
            registry=registry,
        )
        if delete_on_exit:
            delete_metrics_from_gateway(
                gateway_url=gateway_url,
                job_name=job_name,
                grouping_key=grouping_key,
                timeout=timeout,
            )
