"""
Métricas OpenTelemetry para o connection pool do SQLAlchemy.

Expõe db_pool_active_connections e db_pool_idle_connections para o Prometheus,
compatível com engine síncrona ou assíncrona (AsyncEngine).
"""

from opentelemetry import metrics
from opentelemetry.metrics import CallbackOptions, Observation

from ..solview_logging import get_logger

_logger = get_logger(__name__)


def _get_pool(engine):
    """Obtém o pool a partir de Engine ou AsyncEngine."""
    # AsyncEngine expõe .pool (proxy para sync_engine.pool); Engine expõe .pool
    pool = getattr(engine, "pool", None)
    if pool is None:
        return None
    # NullPool (ex.: SQLite unittest) pode não ter checkedin/checkedout
    if not (hasattr(pool, "checkedout") and hasattr(pool, "checkedin")):
        return None
    return pool


def setup_db_pool_metrics(engine):
    """
    Configura métricas assíncronas do OpenTelemetry para observar
    o connection pool do SQLAlchemy.

    Compatível com:
    - sqlalchemy.engine.Engine (síncrono)
    - sqlalchemy.ext.asyncio.AsyncEngine (usa o pool subjacente)

    Métricas registradas (Prometheus):
    - db_pool_active_connections: conexões atualmente em uso (checked out)
    - db_pool_idle_connections: conexões livres no pool (checked in)
    """
    pool = _get_pool(engine)
    if pool is None:
        _logger.warning(
            "Pool de conexões sem suporte a checkedin/checkedout; métricas de pool não registradas."
        )
        return

    meter = metrics.get_meter("solview.database", None)

    def observe_active_connections(options: CallbackOptions):
        try:
            active = pool.checkedout()
        except Exception:
            active = 0
        yield Observation(active)

    def observe_idle_connections(options: CallbackOptions):
        try:
            idle = pool.checkedin()
        except Exception:
            idle = 0
        yield Observation(idle)

    meter.create_observable_gauge(
        name="db_pool_active_connections",
        callbacks=[observe_active_connections],
        description="Número de conexões de banco de dados atualmente em uso",
        unit="{connections}",
    )
    meter.create_observable_gauge(
        name="db_pool_idle_connections",
        callbacks=[observe_idle_connections],
        description="Número de conexões de banco de dados livres no pool",
        unit="{connections}",
    )

    _logger.info("Métricas de connection pool (db_pool_active_connections, db_pool_idle_connections) registradas.")
