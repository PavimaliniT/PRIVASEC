import os
import secrets
from typing import List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "PRIVASEC"
    PROJECT_FULL_NAME: str = "Privacy-Preserving Intelligent Cyber Defense Platform"
    VERSION: str = "1.0.0"
    API_V1_PREFIX: str = "/api"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    # Security Keys
    SECRET_KEY: str = os.getenv("SECRET_KEY", "privasec-super-secret-development-key-32chars-min-length-99!")
    ENCRYPTION_MASTER_KEY_HEX: str = os.getenv(
        "ENCRYPTION_MASTER_KEY_HEX",
        "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"  # 32 bytes AES-256 key
    )
    HMAC_PEPPER_KEY: str = os.getenv("HMAC_PEPPER_KEY", "privasec-pseudonym-pepper-key-2026-secure")
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./privasec.db")
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    # Session & Security
    SESSION_COOKIE_NAME: str = "privasec_session"
    SESSION_MAX_AGE_SECONDS: int = 86400  # 24 hours
    CSRF_COOKIE_NAME: str = "privasec_csrf"
    
    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000"
    ]

    # Risk Engine Weights
    RISK_WEIGHT_AUTH: float = 0.25
    RISK_WEIGHT_BEHAVIOR: float = 0.20
    RISK_WEIGHT_ML_ANOMALY: float = 0.20
    RISK_WEIGHT_API_SECURITY: float = 0.20
    RISK_WEIGHT_DATA_SENSITIVITY: float = 0.15

    # Storage Paths
    UPLOAD_DIR: str = os.path.join(os.path.dirname(os.path.dirname(__file__)), "storage", "uploads")
    PROCESSED_DIR: str = os.path.join(os.path.dirname(os.path.dirname(__file__)), "storage", "processed")
    MODELS_DIR: str = os.path.join(os.path.dirname(os.path.dirname(__file__)), "ml_artifacts")

    # Audit Hash Chain Genesis
    AUDIT_GENESIS_PREV_HASH: str = "0000000000000000000000000000000000000000000000000000000000000000"

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()

# Ensure storage directories exist
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
os.makedirs(settings.PROCESSED_DIR, exist_ok=True)
os.makedirs(settings.MODELS_DIR, exist_ok=True)
