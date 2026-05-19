"""Fernet symmetric encryption helpers for sensitive PII fields."""
from __future__ import annotations

from cryptography.fernet import Fernet, InvalidToken

from app.core.config import get_settings
from app.core.exceptions import ValidationError


def _get_fernet() -> Fernet:
    settings = get_settings()
    key: str = settings.fernet_key  # base64-urlsafe 32-byte key, set in .env
    try:
        return Fernet(key.encode() if isinstance(key, str) else key)
    except (ValueError, TypeError) as exc:
        raise ValidationError(
            message="Invalid FERNET_KEY configuration",
            details={"hint": "Generate a key with Fernet.generate_key().decode()."},
        ) from exc


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
    except InvalidToken:
        return None
