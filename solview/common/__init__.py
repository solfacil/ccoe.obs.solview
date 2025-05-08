"""
solview.common

Módulo de utilidades e helpers universais compartilhados entre todos os submódulos do Solview.
Inclui funções auxiliares para masking, validação, parsing, manipulação de dados sensíveis, etc.
"""

from .masking import mask_sensitive_data

__all__ = [
    "mask_sensitive_data",
]