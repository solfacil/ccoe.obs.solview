import os
import io
import asyncio
import importlib
import orjson


def test_integration_settings_logger_sink(monkeypatch):
    # 1. Configura env para simular ambiente prd e valores custom
    monkeypatch.setenv("SOLVIEW_LOG_LEVEL", "DEBUG")
    monkeypatch.setenv("SOLVIEW_ENVIRONMENT", "prd")
    monkeypatch.setenv("SOLVIEW_SERVICE_NAME", "super-app")
    monkeypatch.setenv("SOLVIEW_DOMAIN", "dom")
    monkeypatch.setenv("SOLVIEW_SUBDOMAIN", "int")
    monkeypatch.setenv("SOLVIEW_VERSION", "1.2.99")

    # Sempre recarregue o módulo de settings após monkeypatch!
    import solview.settings
    importlib.reload(solview.settings)
    from solview.settings import SolviewSettings

    s = SolviewSettings()
    assert s.service_name_composed == "prd-super-app"
    assert s.log_level == "DEBUG"
    assert s.environment == "prd"
    assert s.service_name == "super-app"
    assert s.domain == "dom"
    assert s.subdomain == "int"
    assert s.version == "1.2.99"

    # 2. Gera instance de LoggingSettings (simulando produção)
    from solview.solview_logging.settings import LoggingSettings
    from solview.solview_logging.core import setup_logger
    log_settings = LoggingSettings(
        log_level=s.log_level,
        environment=s.environment,
        service_name=s.service_name,
        domain=s.domain,
        subdomain=s.subdomain,
        version=s.version
    )

    # 3. Prepara sink custom (BytesIO)
    from solview.solview_logging.sinks import ecs_sink
    from solview import get_logger

    class MemorySink:
        """Sink síncrono para coletar logs em memória (para integração)."""
        def __init__(self):
            self.buf = io.BytesIO()
        def write(self, msg):
            self.buf.write(msg.encode("utf-8"))
        def flush(self):
            pass

    mem_sink = io.BytesIO()  # buffer para ECS sink

    # 4. Setup logger (em prod, usando sink ECS, mas enqueue=False pra sync test)
    def create_sync_sink(settings, outstream):
        def sync_sink(message):
            """Versão síncrona do ECS sink para usar em teste."""
            rec = message.record
            log_message = {
                "@timestamp": rec["time"].strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
                "event": {
                    "created": rec["time"].strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
                    "duration": int(rec["elapsed"].total_seconds() * 1e9),
                },
                "labels": rec["extra"],
                "level": str(rec["level"].name).lower(),
                "message": rec["message"],
                "log": {
                    "file": {"path": rec["file"].path},
                    "level": str(rec["level"].name).lower(),
                    "logger": rec["name"],
                    "module": rec["module"],
                    "origin": {
                        "file": {
                            "line": rec["line"],
                            "name": rec["file"].name,
                        },
                        "function": rec["function"],
                    },
                },
                "process": {
                    "pid": rec["process"].id,
                    "name": rec["process"].name,
                    "thread": {
                        "id": rec["thread"].id,
                        "name": rec["thread"].name,
                    },
                },
                "service": {
                    "environment": settings.environment,
                    "domain": settings.domain,
                    "name": settings.service_name,
                    "subdomain": settings.subdomain,
                    "version": settings.version,
                },
            }
            exception = rec.get("exception")
            if exception is not None:
                log_message["error"] = {
                    "message": str(exception.value),
                    "type": rec["exception"].type.__name__,
                }
            json_message = orjson.dumps(log_message) + b"\n"
            outstream.write(json_message)
            outstream.flush()

        return sync_sink

    # Inicializa o logger do Solview e injeta o sink síncrono do teste
    setup_logger(log_settings)
    from loguru import logger as _logger  # acesso direto para adicionar sink custom só no teste
    _logger.remove()
    _logger.add(create_sync_sink(log_settings, mem_sink), level=log_settings.log_level, enqueue=False)

    # 5. Emite um log completo
    logger = get_logger(__name__)
    logger.bind(foo="bar", user="alice").info("INTEG log: tudo ok")

    # 6. Lê resultado da memória
    mem_sink.seek(0)
    line = mem_sink.read()
    data = orjson.loads(line)
    # 7. Checa todos os campos essenciais (ECS + custom)
    assert data["message"].startswith("INTEG log")
    assert data["service"]["name"] == "super-app"
    assert data["level"] == "info"
    assert data["service"]["environment"] == "prd"
    assert data["labels"]["foo"] == "bar"
    assert data["labels"]["user"] == "alice"
    assert data["service"]["domain"] == "dom"
    assert data["service"]["subdomain"] == "int"
    assert data["service"]["version"] == "1.2.99"
    assert "@timestamp" in data
    assert "event" in data
