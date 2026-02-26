from pydantic import BaseModel

class LoggingSettings(BaseModel):
    """
    Configuração para Logging SolView.

    
    """
    log_level: str = "INFO"
    environment: str = "dev"
    service_name: str = "app"
    domain: str = ""
    subdomain: str = ""
    version: str = "0.1.0"
    ignore_mask: bool = False

    @property
    def service_name_composed(self) -> str:
        if self.environment and self.service_name:
            return f"{self.environment}-{self.service_name}"
        return "-"