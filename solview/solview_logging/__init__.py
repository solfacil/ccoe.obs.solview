"""
solview.logging

Módulo de logging estruturado para o ecossistema SolView (Solfácil).
Fornece configuração unificada e helpers para log estruturado e integração com stacks como Loki, ELK, etc.
"""
from .core import setup_logger

def get_logger(name: str = None):
    from loguru import logger as _logger
    return _logger if name is None else _logger.bind(logger_name=name)

__all__ = ["setup_logger", "get_logger"]
from .settings import LoggingSettings

__all__ = ["setup_logger", "LoggingSettings"]