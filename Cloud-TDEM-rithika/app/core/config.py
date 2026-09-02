"""
Configuration management for TDEM backend
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings"""
    
    # Environment
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    AUTH_MODE: str = os.getenv("AUTH_MODE", "development" if ENVIRONMENT == "development" else "jwt")
    DEBUG: bool = ENVIRONMENT == "development"
    
    # API
    API_VERSION: str = "v1"
    API_TITLE: str = "TDEM Secure Vault API"
    API_DESCRIPTION: str = "Temporal Data Encryption Management System"
    
    # Server
    HOST: str = "127.0.0.1"
    PORT: int = 8000
    RELOAD: bool = DEBUG
    
    # Database (local)
    STORAGE_PATH: str = os.getenv("STORAGE_PATH", "./data/storage")
    METADATA_PATH: str = os.getenv("METADATA_PATH", "./data/metadata")
    
    # Crypto
    CRYPTO_TIME_WINDOW: int = 5  # seconds, for testing
    CRYPTO_KSEED: str = os.getenv("CRYPTO_KSEED", "development-seed-key-32-bytes-min")
    
    # Auth
    DEVELOPMENT_USER_ID: str = "dev_user_001"
    DEVELOPMENT_USER_NAME: str = "Developer"
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "dev-secret-key-change-in-prod")
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    
    # Logging
    LOG_LEVEL: str = "INFO" if not DEBUG else "DEBUG"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()


# Create required directories
def init_directories():
    """Initialize required directories for local storage"""
    os.makedirs(settings.STORAGE_PATH, exist_ok=True)
    os.makedirs(settings.METADATA_PATH, exist_ok=True)
