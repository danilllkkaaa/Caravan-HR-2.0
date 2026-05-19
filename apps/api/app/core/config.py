from __future__ import annotations

from functools import lru_cache
from typing import Any

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_env: str = "development"
    app_debug: bool = False
    app_secret_key: str = "change-me"
    app_allowed_origins: list[str] = ["http://localhost:3000", "http://localhost:5173"]
    app_allowed_origin_regex: str = ""

    # Database
    database_url: str = "postgresql+asyncpg://portal:portal@localhost:5432/portal"
    database_pool_size: int = 20
    database_max_overflow: int = 10
    database_pool_timeout: int = 30

    # Redis
    redis_url: str = "redis://localhost:6379/0"
    redis_cache_ttl: int = 60

    # JWT
    jwt_secret_key: str = "change-me-jwt"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 15
    jwt_refresh_token_expire_days: int = 30

    # Celery
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"

    # MinIO
    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin"
    minio_bucket_sick_leave: str = "sick-leave-documents"
    minio_secure: bool = False

    # Sentry
    sentry_dsn: str = ""
    sentry_traces_sample_rate: float = 0.1
    sentry_environment: str = "development"

    # 1C Integration
    oc_base_url: str = "http://1c-server/hr/hs/"
    oc_username: str = "service_user"
    oc_password: str = "service_password"
    oc_timeout: int = 30

    # Hikvision
    hikvision_hmac_secret: str = "change-me"
    hikvision_attendance_stream: str = "attendance:raw"

    # Account locking
    max_failed_login_attempts: int = 5
    account_lock_minutes: int = 15

    # Firebase
    firebase_credentials_path: str = ""

    # Encryption (Fernet) – generate with: Fernet.generate_key().decode()
    fernet_key: str = "CHANGE_ME_FERNET_KEY_32_BYTES_BASE64=="

    # MinIO personal-data bucket
    minio_bucket_personal_data: str = "personal-data-documents"

    @field_validator("app_allowed_origins", mode="before")
    @classmethod
    def parse_origins(cls, v: Any) -> list[str]:
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    @property
    def cors_allowed_origin_regex(self) -> str | None:
        if self.app_allowed_origin_regex:
            return self.app_allowed_origin_regex
        if self.is_production:
            return None
        return (
            r"^http://("
            r"localhost|127\.0\.0\.1|"
            r"10\.\d{1,3}\.\d{1,3}\.\d{1,3}|"
            r"192\.168\.\d{1,3}\.\d{1,3}|"
            r"172\.(1[6-9]|2\d|3[0-1])\.\d{1,3}\.\d{1,3}"
            r")(:\d+)?$"
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()
