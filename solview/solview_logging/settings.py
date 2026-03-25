"""
Configuração do módulo de logging do Solview.
Expõe LoggingSettings com os campos usados por setup_logger e pelos sinks (service name, environment, etc.).
"""

import os
from pydantic import BaseModel


class LoggingSettings(BaseModel):
    """
    Configuração usada pelo logging estruturado do Solview.
    Campos compatíveis com SolviewSettings para uso em sinks e setup_logger.
    """

    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    environment: str = os.getenv("ENVIRONMENT", "dev")
    service_name: str = os.getenv("SERVICE_NAME", "app")
    domain: str = os.getenv("DOMAIN", "")
    subdomain: str = os.getenv("SUBDOMAIN", "")
    version: str = os.getenv("VERSION", "1.0.1")

    @property
    def service_name_composed(self) -> str:
        """Nome do serviço composto: {environment}-{service_name} (usa valores brutos)."""
        env = (self.environment or "").strip()
        name = (self.service_name or "").strip()
        if not env and not name:
            return "-"
        return f"{env}-{name}" if name else env
