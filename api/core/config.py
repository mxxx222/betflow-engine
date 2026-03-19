"""
Configuration settings for BetFlow Engine API.
"""

import os
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    """Application settings."""
    
    # Database
    POSTGRES_URL: str = Field(default="postgresql://betflow:betflow123@postgres:5432/betflow")
    POSTGRES_HOST: str = Field(default="postgres")
    POSTGRES_PORT: int = Field(default=5432)
    POSTGRES_DB: str = Field(default="betflow")
    POSTGRES_USER: str = Field(default="betflow")
    POSTGRES_PASSWORD: str = Field(default="betflow123")
    
    # API Configuration
    API_RATE_LIMIT: int = Field(default=100)
    JWT_SECRET: str = Field(default="your-super-secret-jwt-key-change-in-production")
    ADMIN_EMAIL: str = Field(default="admin@betflow.local")
    
    # Security
    API_KEY_HASH_SALT: str = Field(default="your-api-key-salt")
    CORS_ORIGINS: List[str] = Field(default=["http://localhost:3000", "http://localhost:8000"])
    
    # External Providers
    ODDS_API_KEY: Optional[str] = Field(default=None)
    SPORTS_MONKS_KEY: Optional[str] = Field(default=None)
    BETFAIR_APP_KEY: Optional[str] = Field(default=None)
    BETFAIR_SESSION_TOKEN: Optional[str] = Field(default=None)

    # AI Provider Configuration
    AI_PROVIDER: str = Field(default="openrouter")
    OPENROUTER_API_KEY: Optional[str] = Field(default=None)
    OPENROUTER_MODEL: str = Field(default="cognitivecomputations/dolphin-mistral-7b")
    VENICE_API_KEY: Optional[str] = Field(default=None)
    VENICE_MODEL: str = Field(default="venice-uncensored")
    
    # n8n Configuration
    N8N_WEBHOOK_URL: str = Field(default="http://n8n:5678")
    N8N_BASIC_AUTH_ACTIVE: bool = Field(default=True)
    N8N_BASIC_AUTH_USER: str = Field(default="admin")
    N8N_BASIC_AUTH_PASSWORD: str = Field(default="admin123")
    
    # Monitoring
    PROMETHEUS_PORT: int = Field(default=9090)
    GRAFANA_PORT: int = Field(default=3001)
    
    # Development
    DEBUG: bool = Field(default=True)
    LOG_LEVEL: str = Field(default="INFO")

    # FAP (Field Audit Platform) Settings - Optional
    FAP_DEBUG: Optional[bool] = Field(default=None)
    FAP_SECRET_KEY: Optional[str] = Field(default=None)
    FAP_DATABASE_URL: Optional[str] = Field(default=None)
    FAP_DB_ENCRYPT_KEY: Optional[str] = Field(default=None)
    FAP_MQTT_BROKER: Optional[str] = Field(default=None)
    FAP_MQTT_PORT: Optional[int] = Field(default=None)
    FAP_MQTT_USER: Optional[str] = Field(default=None)
    FAP_MQTT_PASSWORD: Optional[str] = Field(default=None)
    FAP_TRAFICOM_COMPLIANCE: Optional[bool] = Field(default=None)
    FAP_GDPR_MODE: Optional[bool] = Field(default=None)
    FAP_AUDIT_RETENTION: Optional[int] = Field(default=None)

    class Config:
        env_file = ".env"
        case_sensitive = True

# Global settings instance
settings = Settings()
