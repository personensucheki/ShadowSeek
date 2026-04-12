import base64
import hashlib

from cryptography.fernet import Fernet, InvalidToken
from flask import current_app


def _derive_fernet_key() -> bytes:
    """
    Derive a stable Fernet key from SECRET_KEY (no extra env var required).

    - Fernet requires a 32-byte urlsafe-base64 key.
    - We hash SECRET_KEY with SHA-256 and base64 it.
    """
    secret = (current_app.config.get("SECRET_KEY") or "").encode("utf-8")
    if not secret:
        raise RuntimeError("SECRET_KEY fehlt; kann Token-Verschluesselung nicht initialisieren.")
    digest = hashlib.sha256(secret).digest()
    return base64.urlsafe_b64encode(digest)


def _fernet() -> Fernet:
    return Fernet(_derive_fernet_key())


def encrypt_text(value: str | None) -> str | None:
    if value is None:
        return None
    if value == "":
        return ""
    token = _fernet().encrypt(value.encode("utf-8"))
    return token.decode("utf-8")


def decrypt_text(value: str | None) -> str | None:
    if value is None:
        return None
    if value == "":
        return ""
    try:
        plain = _fernet().decrypt(value.encode("utf-8"))
        return plain.decode("utf-8")
    except InvalidToken:
        # Key changed or DB data corrupted; treat as missing.
        return None

