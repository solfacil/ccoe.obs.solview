from pydantic import BaseModel

class LoggingSettings(BaseModel):
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
    log_level: str = "INFO"
    environment: str = "development"
    service_name: str = "app"
    domain: str = ""
    subdomain: str = ""
    version: str = "0.1.0"

    @property
    def service_name_composed(self) -> str:
        if self.environment and self.service_name:
            return f"{self.environment}-{self.service_name}"
        return "-"