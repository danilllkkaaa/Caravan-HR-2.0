"""MinIO / S3-compatible object storage helpers."""
from __future__ import annotations

import uuid

from minio import Minio

from app.core.config import get_settings

_client: Minio | None = None


def get_minio_client() -> Minio:
    global _client
    if _client is None:
        settings = get_settings()
        _client = Minio(
            settings.minio_endpoint,
            access_key=settings.minio_access_key,
            secret_key=settings.minio_secret_key,
            secure=settings.minio_secure,
        )
    return _client


def generate_upload_url(
    bucket: str,
    prefix: str = "uploads",
    expires_seconds: int = 600,
) -> tuple[str, str]:
    """Return (presigned_put_url, object_key)."""
    from datetime import timedelta

    client = get_minio_client()
    object_key = f"{prefix}/{uuid.uuid4()}"
    url = client.presigned_put_object(
        bucket, object_key, expires=timedelta(seconds=expires_seconds)
    )
    return url, object_key


def generate_download_url(
    bucket: str,
    object_key: str,
    expires_seconds: int = 3600,
) -> str:
    """Return presigned GET URL."""
    from datetime import timedelta

    client = get_minio_client()
    return client.presigned_get_object(
        bucket, object_key, expires=timedelta(seconds=expires_seconds)
    )
