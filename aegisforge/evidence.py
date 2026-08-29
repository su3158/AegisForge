from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .ids import new_id

SECRET_PATTERNS = [
    re.compile(r"(?i)(authorization:\s*bearer\s+)[^\s]+"),
    re.compile(r"(?i)(api[_-]?key[\"']?\s*[:=]\s*[\"']?)[^\"'\s,]+"),
    re.compile(r"(?i)(cookie:\s*)[^\r\n]+"),
]


def redact(text: str) -> str:
    for pattern in SECRET_PATTERNS:
        text = pattern.sub(r"\1[REDACTED]", text)
    return text


@dataclass(frozen=True)
class EvidenceRecord:
    id: str
    type: str
    sha256: str
    path: str
    redacted: bool
    timestamp: str


def write_evidence(base_dir: Path, evidence_type: str, payload: Any, raw: bool = False) -> EvidenceRecord:
    # Hash the original observation, but store redacted text by default.
    base_dir.mkdir(parents=True, exist_ok=True)
    evidence_id = new_id()
    text = payload if isinstance(payload, str) else json.dumps(payload, indent=2, sort_keys=True)
    redacted_text = text if raw else redact(text)
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    path = base_dir / f"{evidence_id}.txt"
    path.write_text(redacted_text, encoding="utf-8")
    return EvidenceRecord(evidence_id, evidence_type, digest, str(path), not raw, datetime.now(UTC).isoformat())
