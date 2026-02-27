import sys
import logging
import asyncio
import os
from typing import Any, Optional
from loguru import logger
from loguru._handler import Message
from .sinks import ecs_sink
from .masking import DataMasker

from solview.config import get_settings
settings = get_settings()

class PropagateToLogging(logging.Handler):
    def emit(self, record: logging.LogRecord) -> None:
        logging.getLogger(record.name).handle(record)

def trace_context_filter(record):
    try:
        from opentelemetry.trace import get_current_span, format_trace_id, format_span_id
        span = get_current_span()
        trace_id = "N/A"
        span_id = "N/A"
        if span and hasattr(span, "get_span_context"):
            ctx = span.get_span_context()
            if getattr(ctx, "is_valid", None) and ctx.is_valid:
                trace_id = format_trace_id(ctx.trace_id)
                span_id = format_span_id(ctx.span_id)
        record["extra"]["trace_id"] = trace_id
        record["extra"]["span_id"] = span_id
    except Exception:
        record["extra"]["trace_id"] = "N/A"
        record["extra"]["span_id"] = "N/A"
    return True


def create_masking_filter():
    """
    Create a filter function that masks sensitive data in log messages.
        
    Returns:
        Filter function for loguru
    """
    def masking_filter(record):
        """Filter that sanitizes and masks sensitive data in log messages."""
        try:
            # Check if ignore_mask is set in the log call (via extra)
            # Se não estiver no extra, usa False (sempre mascarar por padrão)
            ignore_mask = record["extra"].pop("ignore_mask", False)
            masker = DataMasker(ignore_mask=ignore_mask)
            
            # Sanitize the message
            original_message = record["message"]
            sanitized_message = masker.sanitize_message(original_message)
            
            # Add trace_id from environment if present
            trace_id = os.environ.get("TRACE_ID")
            if trace_id:
                sanitized_message = f"[trace_id={trace_id}] {sanitized_message}"
            
            record["message"] = sanitized_message
            
            # Also sanitize exception message if present
            if record.get("exception"):
                exception = record["exception"]
                if hasattr(exception, "value") and exception.value:
                    exception_msg = str(exception.value)
                    record["exception"].value = type(exception.value)(masker.mask_sensitive_data(exception_msg))
        except Exception:
            # If masking fails, keep original message
            pass
        
        return True
    
    return masking_filter

def setup_logger(enqueue: Optional[bool] = None) -> None:
    """
    Configura o logger do SolView usando a configuração fornecida.
    Ajusta automaticamente `enqueue` para evitar erro de event loop em scripts síncronos.
    
    Args:
        enqueue: Se deve usar enqueue para async (None = auto-detect)
    """

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

    # Create masking filter
    masking_filter = create_masking_filter()
    
    # Combine filters: first masking, then trace context
    def combined_filter(record):
        masking_filter(record)
        trace_context_filter(record)
        return True
    
    # Configurar cores personalizadas para os níveis (todos os ambientes)
    logger.level("TRACE", color="<cyan>")
    logger.level("DEBUG", color="<blue>")
    logger.level("INFO", color="<green>")
    logger.level("SUCCESS", color="<green>")
    logger.level("WARNING", color="<yellow>")
    logger.level("ERROR", color="<red>")
    logger.level("CRITICAL", color="<red><bold>")

    if settings.environment == "unittest":
        logger.add(PropagateToLogging(), level=settings.log_level)
        logger.add(
            sink=sys.stderr,  # Usa stderr para aparecer como "Captured log call" no pytest
            format=(
                "{time:YYYY-MM-DD HH:mm:ss.SSS} | "
                "{level: <8} | "
                "{name}:{function}:{line} | "
                "trace_id={extra[trace_id]} | "
                "span_id={extra[span_id]} | "
                "{message}"
            ),
            level=settings.log_level,
            diagnose=False,
            catch=True,
            filter=combined_filter,
            colorize=True,  # Sem cores para melhor legibilidade em testes
        )
    # Ambiente dev: formato legível colorido
    else:
        logger.add(
            sink=sys.stdout,
            format=(
                "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
                "<level>{level: <8}</level> | "
                "<cyan>{name}:{function}:{line}</cyan> | "
                "<yellow>trace_id={extra[trace_id]}</yellow> | "
                "<yellow>span_id={extra[span_id]}</yellow> | "
                "<level>{message}</level>"
            ),
            level=settings.log_level,
            diagnose=False,
            catch=True,
            filter=combined_filter,
            colorize=True,
        )

    _redirect_std_logging()
    # _exclude_uvicorn_logs()

def _create_async_sink():
    async def sink_wrapper(message: Message):
        await ecs_sink(message)
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
    logging.getLogger("uvicorn.access").setLevel(logging.INFO)
    logging.getLogger("uvicorn.error").setLevel(logging.ERROR)
    logging.getLogger("uvicorn").setLevel(logging.INFO)
