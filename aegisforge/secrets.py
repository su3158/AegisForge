from __future__ import annotations

import base64
import hashlib

from cryptography.fernet import Fernet, InvalidToken

from .errors import AegisForgeError, ErrorCode


def _fernet(master_key: str | None) -> Fernet:
    if not master_key:
        raise AegisForgeError(ErrorCode.invalid_config, "AEGISFORGE_SECRET_KEY is required")
    digest = hashlib.sha256(master_key.encode("utf-8")).digest()
    return Fernet(base64.urlsafe_b64encode(digest))


def encrypt_secret(value: str, master_key: str | None) -> str:
    return _fernet(master_key).encrypt(value.encode("utf-8")).decode("ascii")


def decrypt_secret(ciphertext: str, master_key: str | None) -> str:
    try:
        return _fernet(master_key).decrypt(ciphertext.encode("ascii")).decode("utf-8")
    except InvalidToken as exc:
        # Fail closed: a wrong key must never turn into an empty or guessed secret.
        raise AegisForgeError(ErrorCode.invalid_config, "secret decrypt failed") from exc
