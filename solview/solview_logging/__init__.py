"""
solview.logging

Módulo de logging estruturado para o ecossistema SolView (Solfácil).
Fornece configuração unificada e helpers para log estruturado e integração com stacks como Loki, ELK, etc.
"""
from .core import setup_logger
from .settings import LoggingSettings

__all__ = ["setup_logger", "LoggingSettings"]