import os
from pathlib import Path
from pydantic import BaseModel, Field, model_validator
from dotenv import load_dotenv

# Carrega o .env se existir
def _try_load_dotenv():
    for parent in [Path('.').resolve()] + list(Path('.').resolve().parents):
        dotenv_path = parent / ".env"
        if dotenv_path.exists():
            load_dotenv(dotenv_path)
            break

_try_load_dotenv()


class TracingSettings(BaseModel):
    """
    Configuração para Tracing SolView.
    """
    otlp_exporter_protocol: str = "grpc"
    otlp_exporter_host: str = "localhost"
    otlp_exporter_port: int = 4317
    otlp_exporter_http_encrypted: bool = False
    otlp_agent_auth_token: str = ""
    otlp_sqlalchemy_enable_commenter: bool = False
    trace_sampler: str = "always_on"
    trace_sampling_ratio: float = 1.0

class MetricsSettings(BaseModel):
    """
    Configuração para Metrics SolView.
    """
    metrics_enabled: bool = True
    metrics_port: int = 9090
    metrics_path: str = "/metrics"


class SolviewSettings(BaseModel):
    """
    Configurações globais do Solview.
    """
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    # Raw environment value from .env; effective mapping below
    environment: str = os.getenv("ENVIRONMENT", "dev")
    service_name: str = os.getenv("SERVICE_NAME", "app")
    domain: str = os.getenv("DOMAIN", "")
    subdomain: str = os.getenv("SUBDOMAIN", "")
    version: str = os.getenv("VERSION", "1.0.1")
    # Namespace semântico OTEL (ex.: time/produto ou domínio)
    service_namespace: str = os.getenv("OTEL_SERVICE_NAMESPACE", os.getenv("SERVICE_NAMESPACE", "solview"))
    
    # Settings
    ignore_mask: bool = os.getenv("IGNORE_MASK", False)
    tracing_settings: TracingSettings = TracingSettings()
    metrics_settings: MetricsSettings = MetricsSettings()
    
    # Memory profiling configuration
    enable_memory_profiling: bool = os.getenv("ENABLE_MEMORY_PROFILING", "false").lower() == "true" # enabled impacting the performance of the application
    #recomendation: local=1.0, staging=0.1, production=0.01, production_incident=0.05
    sampling_memory_profiling: float = float(os.getenv("SAMPLING_MEMORY_PROFILING", "1.0"))
    # Test/unittest: use console exporter instead of OTLP (evita exportar para fora em testes)
    use_console_exporter_on_unittest: bool = False

    @model_validator(mode="before")
    @classmethod
    def _move_otlp_into_tracing_settings(cls, data):
        """Permite passar otlp_exporter_* no root; move para tracing_settings."""
        if not isinstance(data, dict):
            return data
        otlp_keys = {
            "otlp_exporter_protocol", "otlp_exporter_host", "otlp_exporter_port",
            "otlp_exporter_http_encrypted", "otlp_agent_auth_token",
            "otlp_sqlalchemy_enable_commenter", "trace_sampler", "trace_sampling_ratio",
        }
        root_otlp = {k: data.pop(k) for k in otlp_keys if k in data}
        if not root_otlp:
            return data
        existing = data.get("tracing_settings")
        if isinstance(existing, dict):
            data["tracing_settings"] = {**existing, **root_otlp}
        else:
            data["tracing_settings"] = root_otlp
        return data

    def _normalize_environment(self) -> str:
        env = (self.environment or "").strip().lower()
        prod_aliases = {"prd", "prod", "production"}
        dev_aliases = {"dev", "development", "local", "test", "testing", "qa", "stg", "stage", "staging"}
        if env in prod_aliases:
            return "prd"
        return "dev"  # default and staging/qa/dev map to dev

    @property
    def environment_effective(self) -> str:
        """Return only 'dev' or 'prd'. 'stg' and others are mapped to 'dev'."""
        return self._normalize_environment()

    @property
    def service_name_composed(self) -> str:
        return f"{self.environment_effective}-{self.service_name}"
    
    @property
    def is_production(self) -> bool:
        return self.environment_effective == "prd"

    # Delegação para tracing_settings (compatibilidade com core e callers que usam settings.otlp_*)
    @property
    def otlp_exporter_protocol(self) -> str:
        return self.tracing_settings.otlp_exporter_protocol

    @property
    def otlp_exporter_host(self) -> str:
        return self.tracing_settings.otlp_exporter_host

    @property
    def otlp_exporter_port(self) -> int:
        return self.tracing_settings.otlp_exporter_port

    @property
    def otlp_exporter_http_encrypted(self) -> bool:
        return self.tracing_settings.otlp_exporter_http_encrypted

    @property
    def otlp_agent_auth_token(self) -> str:
        return self.tracing_settings.otlp_agent_auth_token

    @property
    def otlp_sqlalchemy_enable_commenter(self) -> bool:
        return self.tracing_settings.otlp_sqlalchemy_enable_commenter

    @property
    def trace_sampler(self) -> str:
        return self.tracing_settings.trace_sampler

    @property
    def trace_sampling_ratio(self) -> float:
        return self.tracing_settings.trace_sampling_ratio

    @property
    def otlp_endpoint_full(self) -> str:
        """Build complete OTLP endpoint URL"""
        t = self.tracing_settings
        if t.otlp_exporter_protocol.lower() == "grpc":
            return f"{t.otlp_exporter_host}:{t.otlp_exporter_port}"
        scheme = "https" if t.otlp_exporter_http_encrypted else "http"
        return f"{scheme}://{t.otlp_exporter_host}:{t.otlp_exporter_port}"

    def as_dict(self):
        return self.dict()

    def __str__(self):
        return (f"[{self.environment}] {self.service_name} "
                f"{self.domain}/{self.subdomain} v{self.version} ({self.log_level})")