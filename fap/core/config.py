"""
FAP Core Configuration
Settings and environment configuration for Field Audit Platform
"""

import os
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings for FAP"""
    
    # Application
    app_name: str = "FAP - Field Audit Platform"
    version: str = "0.1.0"
    debug: bool = Field(default=False, env="FAP_DEBUG")
    
    # Security
    secret_key: str = Field(default="demo-secret-key-change-in-production", env="FAP_SECRET_KEY")
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # Database
    database_url: str = Field(default="sqlite:///./fap_demo.db", env="FAP_DATABASE_URL")
    database_encrypt_key: str = Field(default="demo-key-32-chars-change-in-prod", env="FAP_DB_ENCRYPT_KEY")
    
    # Authentication
    azure_tenant_id: Optional[str] = Field(default=None, env="AZURE_TENANT_ID")
    azure_client_id: Optional[str] = Field(default=None, env="AZURE_CLIENT_ID")
    azure_client_secret: Optional[str] = Field(default=None, env="AZURE_CLIENT_SECRET")
    
    # MQTT for device integration
    mqtt_broker: str = Field(default="localhost", env="FAP_MQTT_BROKER")
    mqtt_port: int = Field(default=8883, env="FAP_MQTT_PORT")  # TLS port
    mqtt_username: Optional[str] = Field(default=None, env="FAP_MQTT_USER")
    mqtt_password: Optional[str] = Field(default=None, env="FAP_MQTT_PASSWORD")
    
    # Finnish Compliance
    traficom_compliance: bool = Field(default=True, env="FAP_TRAFICOM_COMPLIANCE")
    gdpr_mode: bool = Field(default=True, env="FAP_GDPR_MODE")
    
    # Audit settings
    audit_retention_days: int = Field(default=2555, env="FAP_AUDIT_RETENTION")  # 7 years
    max_audit_sessions: int = Field(default=10, env="FAP_MAX_SESSIONS")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"  # Ignore extra fields from .env


# Global settings instance
settings = Settings()