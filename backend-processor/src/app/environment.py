"""
🌍 Environment Configuration - Backend Processor

Configuração de ambiente para a aplicação de processamento backend.
Integração com Solview para observabilidade completa.
"""

import os
from functools import lru_cache
from typing import List, Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Configurações da aplicação Backend Processor.
    Configurado para service graph generation.
    """
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_ignore_empty=True,
        extra="allow"
    )
    
    # Service Configuration
    service_name: str = Field(default="backend-processor", env="SERVICE_NAME")
    version: str = Field(default="1.0.0", env="SERVICE_VERSION")
    environment: str = Field(default="development", env="ENVIRONMENT")
    debug: bool = Field(default=True, env="DEBUG")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    
    # API Configuration
    api_prefix: str = Field(default="/api/v1", env="API_PREFIX")
    host: str = Field(default="0.0.0.0", env="HOST")
    port: int = Field(default=8001, env="PORT")
    
    # Demo App Integration (Service Communication)
    demo_app_url: str = Field(default="http://solview-demo:8000", env="DEMO_APP_URL")
    demo_app_timeout: int = Field(default=30, env="DEMO_APP_TIMEOUT")
    
    # OpenTelemetry Configuration (Production Ready)
    otel_enabled: bool = Field(default=True, env="OTEL_ENABLED")
    otel_service_name: str = Field(default="backend-processor", env="OTEL_SERVICE_NAME")
    otel_exporter_endpoint: str = Field(default="alloy", env="OTEL_EXPORTER_OTLP_ENDPOINT")
    otel_exporter_port: int = Field(default=4317, env="OTEL_EXPORTER_OTLP_PORT")
    otel_exporter_protocol: str = Field(default="grpc", env="OTEL_EXPORTER_OTLP_PROTOCOL")
    otel_resource_attributes: str = Field(
        default="service.name=backend-processor,service.version=1.0.0,service.namespace=solview,deployment.environment=development",
        env="OTEL_RESOURCE_ATTRIBUTES"
    )
    
    # Service Graph Configuration
    service_graph_enabled: bool = Field(default=True, env="SERVICE_GRAPH_ENABLED")
    
    # Observability Features
    metrics_enabled: bool = Field(default=True, env="METRICS_ENABLED")
    tracing_enabled: bool = Field(default=True, env="TRACING_ENABLED")
    logging_enabled: bool = Field(default=True, env="LOGGING_ENABLED")
    
    # Security Configuration  
    cors_origins: str = Field(default="http://localhost:3000,http://localhost:9090", env="CORS_ORIGINS")
    
    # Processing Configuration
    batch_size: int = Field(default=10, env="BATCH_SIZE")
    processing_interval: int = Field(default=30, env="PROCESSING_INTERVAL_SECONDS")
    retry_attempts: int = Field(default=3, env="RETRY_ATTEMPTS")
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Convert CORS origins string to list."""
        if not self.cors_origins:
            return []
        return [origin.strip() for origin in self.cors_origins.split(",")]
    
    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment.lower() in ["prod", "production", "prd"]
    
    @property
    def otel_endpoint_host(self) -> str:
        """Extract host from OTEL endpoint."""
        ep = self.otel_exporter_endpoint.replace("http://", "").replace("https://", "")
        # strip port if present
        if ":" in ep:
            return ep.split(":", 1)[0]
        return ep
    
    def get_demo_app_endpoint(self, path: str) -> str:
        """Build complete endpoint URL for demo app."""
        return f"{self.demo_app_url.rstrip('/')}{path}"


@lru_cache
def get_settings() -> Settings:
    """
    Get cached settings instance.
    
    Returns:
        Settings: Application settings
    """
    return Settings()
