import os
from pathlib import Path
from pydantic import BaseModel, Field
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
    version: str = os.getenv("SOLVIEW_VERSION", "1.0.1")
    
    # OpenTelemetry Configuration - Production Ready
    otlp_exporter_protocol: str = os.getenv("OTEL_EXPORTER_OTLP_PROTOCOL", "grpc")
    otlp_exporter_host: str = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "localhost")
    otlp_exporter_port: int = int(os.getenv("OTEL_EXPORTER_OTLP_PORT", "4317"))
    otlp_exporter_http_encrypted: bool = os.getenv("OTEL_EXPORTER_OTLP_HTTP_ENCRYPTED", "true").lower() == "true"
    otlp_agent_auth_token: str = os.getenv("OTEL_EXPORTER_OTLP_AUTH_TOKEN", "")
    otlp_sqlalchemy_enable_commenter: bool = os.getenv("OTEL_SQLALCHEMY_ENABLE_COMMENTER", "true").lower() == "true"
    
    # Kubernetes Integration
    k8s_namespace: str = os.getenv("KUBERNETES_NAMESPACE", "default")
    k8s_pod_name: str = os.getenv("HOSTNAME", "")
    k8s_node_name: str = os.getenv("KUBERNETES_NODE_NAME", "")
    
    # Security and Compliance
    enable_data_masking: bool = os.getenv("SOLVIEW_ENABLE_DATA_MASKING", "true").lower() == "true"
    log_retention_days: int = int(os.getenv("SOLVIEW_LOG_RETENTION_DAYS", "30"))
    
    # Metrics Configuration
    metrics_enabled: bool = os.getenv("SOLVIEW_METRICS_ENABLED", "true").lower() == "true"
    metrics_port: int = int(os.getenv("SOLVIEW_METRICS_PORT", "9090"))
    metrics_path: str = os.getenv("SOLVIEW_METRICS_PATH", "/metrics")

    @property
    def service_name_composed(self) -> str:
        return f"{self.environment}-{self.service_name}"
    
    @property
    def is_production(self) -> bool:
        return self.environment in ["prd", "prod", "production"]
    
    @property
    def otlp_endpoint_full(self) -> str:
        """Build complete OTLP endpoint URL"""
        if self.otlp_exporter_protocol.lower() == "grpc":
            return f"{self.otlp_exporter_host}:{self.otlp_exporter_port}"
        else:
            scheme = "https" if self.otlp_exporter_http_encrypted else "http"
            return f"{scheme}://{self.otlp_exporter_host}:{self.otlp_exporter_port}"

    def as_dict(self):
        return self.dict()

    def __str__(self):
        return (f"[{self.environment}] {self.service_name} "
                f"{self.domain}/{self.subdomain} v{self.version} ({self.log_level})")