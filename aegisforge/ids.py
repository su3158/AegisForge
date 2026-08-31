from __future__ import annotations

import secrets
import time
import uuid


def new_id() -> str:
    if hasattr(uuid, "uuid7"):
        return str(uuid.uuid7())

    # ponytail: UUIDv7 fallback for Python 3.12/3.13, replace with stdlib-only when 3.14+.
    ms = int(time.time() * 1000) & ((1 << 48) - 1)
    rand = secrets.randbits(74)
    value = (
        (ms << 80)
        | (0x7 << 76)
        | ((rand >> 62) << 64)
        | (0x2 << 62)
        | (rand & ((1 << 62) - 1))
    )
    return str(uuid.UUID(int=value))
