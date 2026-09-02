import asyncio
import logging

from solview import get_logger
from solview.solview_logging.core import setup_logger
from solview.solview_logging.settings import LoggingSettings


def test_setup_logger_development(capsys):
    s = LoggingSettings(environment="dev", log_level="INFO")
    setup_logger(s)
    logger = get_logger(__name__)
    logger.info("hello dev logger")
    out = capsys.readouterr().out
    assert "hello dev logger" in out or "INFO" in out


def test_intercept_handler_uses_logrecord_metadata(capsys, monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "dev")
    monkeypatch.setenv("LOG_LEVEL", "INFO")

    import importlib
    import solview.settings

    importlib.reload(solview.settings)
    from solview.config import setup_settings
    from solview.settings import SolviewSettings

    setup_settings(SolviewSettings())
    setup_logger()

    stdlib_logger = logging.getLogger("my.test.logger")

    def log_from_helper():
        stdlib_logger.info("stdlib message")

    log_from_helper()
    out = capsys.readouterr().out

    assert "stdlib message" in out
    assert "my.test.logger:log_from_helper:" in out
    assert "InterceptHandler" not in out


def test_setup_logger_production():
    s = LoggingSettings(environment="prd", log_level="INFO")

    async def run_logger():
        setup_logger(s)
        logger = get_logger(__name__)
        logger.info("prod logger initialized")

    asyncio.run(run_logger())
    # O importante é não lançar exceptions nem crashar
