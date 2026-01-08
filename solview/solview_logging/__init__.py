"""
solview.logging

Módulo de logging estruturado para o ecossistema SolView (Solfácil).
Fornece configuração unificada e helpers para log estruturado e integração com stacks como Loki, ELK, etc.
"""
from typing import Any, Optional
from .core import setup_logger
from .settings import LoggingSettings
from .colors import LogColors, get_color_for_level
from .masking import DataMasker


class LoggerWrapper:
    """
    Wrapper around loguru logger that supports ignore_mask parameter.
    
    Usage:
        logger = get_logger()
        logger.info("texto", ignore_mask=True)  # Disable masking for this log
        logger.info("texto")  # Use default masking behavior
    """
    
    def __init__(self, logger_instance):
        self._logger = logger_instance
    
    def _extract_ignore_mask(self, kwargs: dict) -> bool:
        """Extract ignore_mask from kwargs and remove it."""
        return kwargs.pop("ignore_mask", False)
    
    def bind(self, *args, **kwargs):
        """Bind context to logger."""
        return LoggerWrapper(self._logger.bind(*args, **kwargs))
    
    def _get_logger_with_mask(self, ignore_mask: Optional[bool]) -> Any:
        """Get logger with ignore_mask bound if provided."""
        logger_instance = self._logger.bind(ignore_mask=ignore_mask) if ignore_mask is not None else self._logger
        # Usar opt(depth=1) para capturar o contexto correto (quem chamou o logger)
        return logger_instance.opt(depth=1)
    
    def info(self, message: Any, *args, ignore_mask: Optional[bool] = None, **kwargs):
        """Log info message with optional ignore_mask."""
        return self._get_logger_with_mask(ignore_mask).info(message, *args, **kwargs)
    
    def debug(self, message: Any, *args, ignore_mask: Optional[bool] = None, **kwargs):
        """Log debug message with optional ignore_mask."""
        return self._get_logger_with_mask(ignore_mask).debug(message, *args, **kwargs)
    
    def warning(self, message: Any, *args, ignore_mask: Optional[bool] = None, **kwargs):
        """Log warning message with optional ignore_mask."""
        return self._get_logger_with_mask(ignore_mask).warning(message, *args, **kwargs)
    
    def error(self, message: Any, *args, ignore_mask: Optional[bool] = None, **kwargs):
        """Log error message with optional ignore_mask."""
        return self._get_logger_with_mask(ignore_mask).error(message, *args, **kwargs)
    
    def critical(self, message: Any, *args, ignore_mask: Optional[bool] = None, **kwargs):
        """Log critical message with optional ignore_mask."""
        return self._get_logger_with_mask(ignore_mask).critical(message, *args, **kwargs)
    
    def exception(self, message: Any, *args, ignore_mask: Optional[bool] = None, **kwargs):
        """Log exception message with optional ignore_mask."""
        return self._get_logger_with_mask(ignore_mask).exception(message, *args, **kwargs)
    
    def success(self, message: Any, *args, ignore_mask: Optional[bool] = None, **kwargs):
        """Log success message with optional ignore_mask."""
        return self._get_logger_with_mask(ignore_mask).success(message, *args, **kwargs)
    
    def trace(self, message: Any, *args, ignore_mask: Optional[bool] = None, **kwargs):
        """Log trace message with optional ignore_mask."""
        return self._get_logger_with_mask(ignore_mask).trace(message, *args, **kwargs)
    
    def __getattr__(self, name: str):
        """Delegate other attributes to the underlying logger."""
        return getattr(self._logger, name)


def get_logger(name: str = None):
    """
    Get a logger instance with support for ignore_mask parameter.
    
    Args:
        name: Optional logger name
        
    Returns:
        LoggerWrapper instance that supports ignore_mask parameter
        
    Example:
        logger = get_logger()
        logger.info("texto", ignore_mask=True)  # Disable masking
        logger.info("texto")  # Use default masking
    """
    from loguru import logger as _logger
    base_logger = _logger if name is None else _logger.bind(logger_name=name)
    return LoggerWrapper(base_logger)

__all__ = [
    "setup_logger",
    "get_logger",
    "LoggingSettings",
    "LogColors",
    "get_color_for_level",
    "DataMasker",
    "LoggerWrapper",
]