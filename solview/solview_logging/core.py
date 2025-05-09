import sys
import logging
import asyncio
from typing import Any, Optional
from loguru import logger
from loguru._handler import Message
from .settings import LoggingSettings
from .sinks import ecs_sink
from solview.settings import SolviewSettings

def trace_context_filter(record):
    try:
        from opentelemetry.trace import get_current_span, format_trace_id, format_span_id
        span = get_current_span()
        trace_id = None
        span_id = None
        if span and hasattr(span, "get_span_context"):
            ctx = span.get_span_context()
            if getattr(ctx, "is_valid", None) and ctx.is_valid:
                trace_id = format_trace_id(ctx.trace_id)
                span_id = format_span_id(ctx.span_id)
        record["extra"]["trace_id"] = trace_id
        record["extra"]["span_id"] = span_id
    except Exception:
        record["extra"]["trace_id"] = None
        record["extra"]["span_id"] = None
    return True

def setup_logger(settings: SolviewSettings = None, enqueue: bool = None) -> None:
    """
    Configura o logger do SolView usando a configuração fornecida.
    Se nada for passado, instancia as settings globais na hora (igual setup_tracer).
    """
    if settings is None:
        settings = SolviewSettings()

    logger.remove()

    # Detecta se há event loop rodando, para evitar problema em scripts puros
    # O usuário pode forçar override em qualquer situação
    if enqueue is None:
        try:
            asyncio.get_running_loop()
            _enqueue = True
        except RuntimeError:
            _enqueue = False
    else:
        _enqueue = enqueue

    # Ambiente dev
    if settings.environment == "dev":
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
            enqueue=_enqueue,
            backtrace=True,
            catch=True,
            filter=trace_context_filter
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