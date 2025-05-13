import os
from pathlib import Path
from pydantic import BaseModel
from dotenv import load_dotenv

# Carrega o .env se existir
def _try_load_dotenv():
    for parent in [Path('.').resolve()] + list(Path('.').resolve().parents):
        dotenv_path = parent / ".env"
        if dotenv_path.exists():
            load_dotenv(dotenv_path)
            break

_try_load_dotenv()

class SolviewSettings(BaseModel):
    """
    Configurações globais do Solview.
    """
    log_level: str = os.getenv("SOLVIEW_LOG_LEVEL", "INFO")
    environment: str = os.getenv("SOLVIEW_ENVIRONMENT", "dev")
    service_name: str = os.getenv("SOLVIEW_SERVICE_NAME", "app")
    domain: str = os.getenv("SOLVIEW_DOMAIN", "")
    subdomain: str = os.getenv("SOLVIEW_SUBDOMAIN", "")
    version: str = os.getenv("SOLVIEW_VERSION", "1.0.0")
    otlp_exporter_protocol: str = os.getenv("OTEL_EXPORTER_OTLP_PROTOCOL", "grpc")
    otlp_exporter_host: str = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "localhost")
    otlp_sqlalchemy_enable_commenter: bool = os.getenv("OTEL_SQLALCHEMY_ENABLE_COMMENTER", "true").lower() == "true"
    otlp_exporter_http_encrypted: bool = os.getenv("OTEL_EXPORTER_OTLP_HTTP_ENCRYPTED", "false").lower() == "true"
    otlp_agent_auth_token: str = os.getenv("OTEL_EXPORTER_OTLP_AUTH_TOKEN", "")

    @property
    def service_name_composed(self) -> str:
        return f"{self.environment}-{self.service_name}"

    def as_dict(self):
        return self.dict()

    def __str__(self):
        return (f"[{self.environment}] {self.service_name} "
                f"{self.domain}/{self.subdomain} v{self.version} ({self.log_level})")
