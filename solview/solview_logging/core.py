import sys
import logging
from typing import Any, Optional

from loguru import logger
from loguru._handler import Message

from .settings import LoggingSettings
from .sinks import ecs_sink

def setup_logger(settings: Optional[LoggingSettings] = None, enqueue: Optional[bool] = True) -> None:
    """
    Configura o logger do SolView usando a configuração fornecida.

    Em ambiente de desenvolvimento: logs coloridos/human-readables.
    Em produção/homolog: logs JSON ECS para processamento por ferramentas.

    Basta importar em qualquer aplicação Python, executar `setup_logger` no início,
    e usar `from loguru import logger`.

    Args:
        settings (LoggingSettings): Configuração personalizada (pode ser None para padrão).
        enqueue (bool, opcional): Se True, usa fila multiprocessada. Em testes, passe False se precisar.
    """
    if settings is None:
        settings = LoggingSettings()

    logger.remove()
    # Ambiente dev: saída colorida bonitinha no terminal
    if settings.environment == "development":
        logger.add(
            sink=sys.stdout,
            format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}:{function}:{line}</cyan> - <level>{message}</level>",
            level=settings.log_level,
            diagnose=False,
            catch=True,
        )
    else:
        logger.add(
            sink=_create_async_sink(settings),
            level=settings.log_level,
            enqueue=enqueue,
            backtrace=True,
            catch=True,
        )

    _redirect_std_logging()
    _exclude_uvicorn_logs()

def _create_async_sink(settings: LoggingSettings):
    async def sink_wrapper(message: Message):
        await ecs_sink(message, settings)
    return sink_wrapper

def _redirect_std_logging():
    """Redireciona logging padrão Python para Loguru (para capturar tudo)"""
    class InterceptHandler(logging.Handler):
        def emit(self, record: logging.LogRecord) -> None:
            try:
                level = logger.level(record.levelname).name
            except Exception:
                level = record.levelno
            frame, depth = logging.currentframe(), 2
            while frame and frame.f_code.co_filename == logging.__file__:
                frame = frame.f_back
                depth += 1
            logger.opt(depth=depth, exception=record.exc_info).log(
                level, record.getMessage()
            )

    logging.basicConfig(handlers=[InterceptHandler()], level=0)

def _exclude_uvicorn_logs():
    """Diminui verbosidade do Uvicorn (caso rode FastAPI/etc)"""
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.error").setLevel(logging.CRITICAL)
    logging.getLogger("uvicorn").setLevel(logging.WARNING)