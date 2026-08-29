import os
from dataclasses import dataclass
from functools import lru_cache


@dataclass(frozen=True)
class Settings:
    app_name: str = os.getenv("TDEM_APP_NAME", "TDEM Backend")
    environment: str = os.getenv("TDEM_ENVIRONMENT", "development")
    host: str = os.getenv("TDEM_HOST", "0.0.0.0")
    port: int = int(os.getenv("TDEM_PORT", "8000"))
    aws_region: str = os.getenv("TDEM_AWS_REGION", "us-east-1")
    s3_bucket: str | None = os.getenv("TDEM_S3_BUCKET")
    dynamodb_table: str | None = os.getenv("TDEM_DYNAMODB_TABLE")
    secret_name: str | None = os.getenv("TDEM_SECRET_NAME")
    cognito_user_pool_id: str | None = os.getenv("TDEM_COGNITO_USER_POOL_ID")
    cognito_client_id: str | None = os.getenv("TDEM_COGNITO_CLIENT_ID")
    log_level: str = os.getenv("TDEM_LOG_LEVEL", "INFO")
    max_upload_bytes: int = int(os.getenv("TDEM_MAX_UPLOAD_BYTES", str(50 * 1024 * 1024)))
    model_module: str = os.getenv("TDEM_MODEL_MODULE", "major_project.service")
    crypto_module: str = os.getenv("TDEM_CRYPTO_MODULE", "crypto_engine.service")


@lru_cache
def get_settings() -> Settings:
    return Settings()
