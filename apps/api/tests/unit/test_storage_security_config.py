from __future__ import annotations

from app.core import minio as minio_core
from app.core.config import get_settings
from app.core.encryption import decrypt_field, encrypt_field


def test_default_fernet_key_encrypts_and_decrypts() -> None:
    get_settings.cache_clear()

    ciphertext = encrypt_field("sensitive-value")

    assert ciphertext != "sensitive-value"
    assert decrypt_field(ciphertext) == "sensitive-value"


def test_minio_presigned_url_uses_public_endpoint(monkeypatch) -> None:
    monkeypatch.setenv("MINIO_ENDPOINT", "minio:9000")
    monkeypatch.setenv("MINIO_PUBLIC_ENDPOINT", "files.example.com")
    monkeypatch.setenv("MINIO_PUBLIC_SECURE", "true")
    get_settings.cache_clear()
    minio_core._presign_client = None

    upload_url, object_key = minio_core.generate_upload_url(
        "documents",
        prefix="employee/test",
    )

    assert object_key.startswith("employee/test/")
    assert upload_url.startswith("https://files.example.com/documents/employee/test/")
    assert "X-Amz-Signature=" in upload_url

    get_settings.cache_clear()
    minio_core._presign_client = None
