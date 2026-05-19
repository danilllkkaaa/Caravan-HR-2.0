"""Fernet symmetric encryption helpers for sensitive PII fields."""
from __future__ import annotations

from cryptography.fernet import Fernet, InvalidToken

from app.core.config import get_settings


def _get_fernet() -> Fernet:
    settings = get_settings()
    key: str = settings.fernet_key  # base64-urlsafe 32-byte key, set in .env
    return Fernet(key.encode() if isinstance(key, str) else key)


def encrypt_field(plaintext: str) -> str:
    """Encrypt *plaintext* and return a URL-safe base64 ciphertext string."""
    return _get_fernet().encrypt(plaintext.encode()).decode()


def decrypt_field(ciphertext: str) -> str:
    """Decrypt a ciphertext string.  Raises ``InvalidToken`` if tampered."""
    return _get_fernet().decrypt(ciphertext.encode()).decode()


def decrypt_field_safe(ciphertext: str | None) -> str | None:
    """Return decrypted value or ``None`` if *ciphertext* is falsy or invalid."""
    if not ciphertext:
        return None
    try:
        return decrypt_field(ciphertext)
    except (InvalidToken, Exception):
        return None
