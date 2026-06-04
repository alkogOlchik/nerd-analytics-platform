from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    DATABASE_URL: str = "postgresql+asyncpg://postgres:password@localhost:5436/nerd_db"
    ANALYTICS_DATABASE_URL: str = (
        "postgresql+asyncpg://postgres:password@localhost:5436/nerd_analytics_db"
    )
    SECRET_KEY: str = "change-me-in-production-use-openssl-rand-hex-32"
    KAFKA_URL: str = "localhost:9092"
    ML_SERVICE_URL: str = "http://localhost:8091"
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    ML_OLLAMA_FALLBACK: bool = True
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    APP_SERVICE_URL: str = "http://127.0.0.1:8001"
    GATEWAY_PORT: int = 8000
    APP_PORT: int = 8001
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GITHUB_CLIENT_ID: str = ""
    GITHUB_CLIENT_SECRET: str = ""
    OAUTH_REDIRECT_URI: str = "http://127.0.0.1:8001/auth/oauth/callback"

    S3_BUCKET_NAME: str = "nerd-files"
    S3_REGION: str = "us-east-1"
    S3_ACCESS_KEY: str = "minioadmin"
    S3_SECRET_KEY: str = "minioadmin"
    S3_ENDPOINT_URL: str = "http://localhost:9000"
    S3_PUBLIC_URL_PREFIX: str | None = None
    S3_PREFIX: str = "uploads"
    LOCAL_UPLOAD_DIR: str = "backend/storage/uploads"
    FILE_UPLOAD_MAX_BYTES: int = 10 * 1024 * 1024

    @property
    def sync_database_url(self) -> str:
        return self.DATABASE_URL.replace("+asyncpg", "")

    @property
    def s3_configured(self) -> bool:
        return bool(self.S3_BUCKET_NAME and self.S3_ACCESS_KEY and self.S3_SECRET_KEY)


@lru_cache
def get_settings() -> Settings:
    return Settings()
