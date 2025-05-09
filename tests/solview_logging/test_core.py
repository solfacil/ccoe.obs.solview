import asyncio
from solview.solview_logging.core import setup_logger
from solview.solview_logging.settings import LoggingSettings
from loguru import logger

def test_setup_logger_development(capsys):
    s = LoggingSettings(environment="stg", log_level="INFO")
    setup_logger(s)
    logger.info("hello dev logger")
    out = capsys.readouterr().out
    assert "hello dev logger" in out or "INFO" in out

def test_setup_logger_production():
    s = LoggingSettings(environment="prd", log_level="INFO")
    async def run_logger():
        setup_logger(s)
    asyncio.run(run_logger())
    # O importante é não lançar exceptions nem crashar