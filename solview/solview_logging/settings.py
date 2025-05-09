from pydantic_settings import BaseSettings
from pydantic import Field

class LoggingSettings(BaseSettings):
    """
    Configuração para Logging SolView.

    Exemplo de uso:
        LoggingSettings(
            log_level="INFO", 
            environment="production",
            service_name="minha-api",
            domain="solarview",
            subdomain="observabilidade",
            version="1.0.0"
        )
    """
    log_level: str = Field("INFO", env="SOLVIEW_LOG_LEVEL")
    environment: str = Field("dev", env="SOLVIEW_ENVIRONMENT")
    service_name: str = Field("app", env="SOLVIEW_SERVICE_NAME")
    domain: str = ""
    subdomain: str = ""
    version: str = "0.1.0"

    @property
    def service_name_composed(self) -> str:
        if self.environment and self.service_name:
            return f"{self.environment}-{self.service_name}"
        return "-"