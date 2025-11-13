"""
Configuration Management for Sherlock SRE

Loads configuration from environment variables with validation.
Uses Pydantic for type safety and validation.
"""

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    """
    Application settings with validation

    All settings can be overridden via environment variables.
    Example: ANTHROPIC_API_KEY=sk-ant-... python main.py
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # AI/ML
    anthropic_api_key: str = Field(
        ...,
        description="Anthropic API key for Claude"
    )

    # Slack
    slack_bot_token: Optional[str] = Field(
        None,
        description="Slack bot token (xoxb-...)"
    )
    slack_app_token: Optional[str] = Field(
        None,
        description="Slack app token (xapp-...)"
    )
    slack_signing_secret: Optional[str] = Field(
        None,
        description="Slack signing secret for request verification"
    )
    slack_channel: str = Field(
        default="#incidents",
        description="Default Slack channel for alerts"
    )

    # Kubernetes
    kubeconfig_path: Optional[str] = Field(
        None,
        description="Path to kubeconfig file (optional, uses in-cluster config if not set)"
    )

    # Database
    postgres_host: str = Field(default="localhost")
    postgres_port: int = Field(default=5432)
    postgres_db: str = Field(default="sherlock")
    postgres_user: str = Field(default="sherlock")
    postgres_password: str = Field(default="")

    # Redis
    redis_host: str = Field(default="localhost")
    redis_port: int = Field(default=6379)
    redis_password: Optional[str] = Field(default=None)

    # Vector Database (Weaviate)
    weaviate_url: str = Field(default="http://localhost:8080")
    weaviate_api_key: Optional[str] = Field(default=None)

    # Monitoring Sources
    prometheus_url: str = Field(default="http://localhost:9090")
    elasticsearch_host: str = Field(default="localhost")
    elasticsearch_port: int = Field(default=9200)
    elasticsearch_user: Optional[str] = Field(default=None)
    elasticsearch_password: Optional[str] = Field(default=None)

    # Cloud Providers (optional)
    aws_region: str = Field(default="us-east-1")
    aws_access_key_id: Optional[str] = Field(default=None)
    aws_secret_access_key: Optional[str] = Field(default=None)

    azure_subscription_id: Optional[str] = Field(default=None)
    azure_tenant_id: Optional[str] = Field(default=None)
    azure_client_id: Optional[str] = Field(default=None)
    azure_client_secret: Optional[str] = Field(default=None)

    gcp_project_id: Optional[str] = Field(default=None)
    gcp_credentials_path: Optional[str] = Field(default=None)

    # Application Settings
    log_level: str = Field(default="INFO")
    environment: str = Field(default="development")

    # Feature Flags
    enable_auto_remediation: bool = Field(
        default=False,
        description="Enable auto-remediation (DANGEROUS! Start with False)"
    )
    enable_predictive_alerts: bool = Field(default=True)
    enable_incident_learning: bool = Field(default=True)

    # Performance
    collector_timeout_seconds: int = Field(default=30)
    ai_cache_ttl_seconds: int = Field(default=3600)  # 1 hour

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        v = v.upper()
        if v not in valid_levels:
            raise ValueError(f"log_level must be one of {valid_levels}")
        return v

    @field_validator("environment")
    @classmethod
    def validate_environment(cls, v: str) -> str:
        valid_envs = ["development", "staging", "production"]
        v = v.lower()
        if v not in valid_envs:
            raise ValueError(f"environment must be one of {valid_envs}")
        return v

    @property
    def postgres_url(self) -> str:
        """PostgreSQL connection URL"""
        return f"postgresql://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"

    @property
    def redis_url(self) -> str:
        """Redis connection URL"""
        if self.redis_password:
            return f"redis://:{self.redis_password}@{self.redis_host}:{self.redis_port}/0"
        return f"redis://{self.redis_host}:{self.redis_port}/0"

    @property
    def is_production(self) -> bool:
        """Check if running in production"""
        return self.environment == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development"""
        return self.environment == "development"


# Global settings instance
settings = Settings()
