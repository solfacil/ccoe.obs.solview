"""
⚙️ Environment Configuration

Configurações de ambiente para a aplicação demo.
Utiliza Pydantic Settings para validação e tipo-safety.
"""

from functools import lru_cache
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Configurações da aplicação com validação."""
    
    # === Application Settings ===
    service_name: str = Field(default="solview-demo-app", env="SOLVIEW_SERVICE_NAME")
    version: str = Field(default="1.0.0", env="SOLVIEW_VERSION")
    environment: str = Field(default="development", env="SOLVIEW_ENVIRONMENT")
    log_level: str = Field(default="INFO", env="SOLVIEW_LOG_LEVEL")
    
    # === Server Settings ===
    host: str = Field(default="0.0.0.0", env="HOST")
    port: int = Field(default=8000, env="PORT")
    debug: bool = Field(default=False, env="DEBUG")
    
    # === OpenTelemetry Settings ===
    otel_enabled: bool = Field(default=True, env="OTEL_ENABLED")
    otel_service_name: str = Field(default="solview-demo-app", env="OTEL_SERVICE_NAME")
    otel_service_version: str = Field(default="1.0.0", env="OTEL_SERVICE_VERSION")
    otel_exporter_endpoint: str = Field(
        default="http://otel-collector:4317", 
        env="OTEL_EXPORTER_OTLP_ENDPOINT"
    )
    otel_resource_attributes: str = Field(
        default="service.name=solview-demo-app,service.version=1.0.0,service.namespace=solview",
        env="OTEL_RESOURCE_ATTRIBUTES"
    )
    
    # === Observability Features ===
    service_graph_enabled: bool = Field(default=True, env="SERVICE_GRAPH_ENABLED")
    metrics_enabled: bool = Field(default=True, env="METRICS_ENABLED")
    tracing_enabled: bool = Field(default=True, env="TRACING_ENABLED")
    logging_enabled: bool = Field(default=True, env="LOGGING_ENABLED")
    
    # === External Services ===
    redis_url: str = Field(default="redis://redis:6379", env="REDIS_URL")
    database_url: Optional[str] = Field(default=None, env="DATABASE_URL")
    
    # === API Settings ===
    api_prefix: str = Field(default="/api", env="API_PREFIX")
    api_version: str = Field(default="v1", env="API_VERSION")
    
    # === CORS Settings ===
    cors_origins: str = Field(
        default="http://localhost:3000,http://localhost:9090",
        env="CORS_ORIGINS"
    )
    
    # === Rate Limiting ===
    rate_limit_enabled: bool = Field(default=True, env="RATE_LIMIT_ENABLED")
    rate_limit_requests: int = Field(default=100, env="RATE_LIMIT_REQUESTS")
    rate_limit_window: int = Field(default=60, env="RATE_LIMIT_WINDOW")
    
    class Config:
        """Pydantic configuration."""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        
    @property
    def is_development(self) -> bool:
        """Verifica se está em modo desenvolvimento."""
        return self.environment.lower() in ("development", "dev", "local")
    
    @property
    def is_production(self) -> bool:
        """Verifica se está em modo produção."""
        return self.environment.lower() in ("production", "prod")
    
    @property
    def is_testing(self) -> bool:
        """Verifica se está em modo teste."""
        return self.environment.lower() in ("testing", "test")
    
    @property
    def otel_resource_dict(self) -> dict[str, str]:
        """Converte OTEL_RESOURCE_ATTRIBUTES para dicionário."""
        if not self.otel_resource_attributes:
            return {}
        
        result = {}
        for attr in self.otel_resource_attributes.split(","):
            if "=" in attr:
                key, value = attr.strip().split("=", 1)
                result[key.strip()] = value.strip()
        return result
    
    @property 
    def cors_origins_list(self) -> list[str]:
        """Converte CORS_ORIGINS string para lista."""
        if not self.cors_origins:
            return []
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache()
def get_settings() -> Settings:
    """
    Obtém configurações da aplicação com cache.
    
    Returns:
        Settings: Instância das configurações
    """
    return Settings()


# Instância global para facilitar importação
settings = get_settings()
