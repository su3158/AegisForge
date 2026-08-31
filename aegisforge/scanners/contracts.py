from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from hashlib import sha256
from typing import Any, Protocol
from uuid import uuid4


class _StrEnum(str, Enum):
    pass


class Severity(_StrEnum):
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class FindingStatus(_StrEnum):
    CANDIDATE = "candidate"
    CONFIRMED = "confirmed"
    ERROR = "error"


class ScanProfile(_StrEnum):
    QUICK = "quick"
    STANDARD = "standard"


class ScanState(_StrEnum):
    CREATED = "created"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


@dataclass(frozen=True)
class Evidence:
    type: str
    body: str
    source: str
    metadata: dict[str, Any] = field(default_factory=dict)
    id: str = field(default_factory=lambda: f"E-{uuid4().hex[:12]}")
    timestamp: str = field(default_factory=lambda: datetime.now(UTC).isoformat())

    @property
    def sha256(self) -> str:
        return sha256(self.body.encode("utf-8", errors="replace")).hexdigest()


@dataclass
class Finding:
    title: str
    category: str
    severity: Severity = Severity.INFO
    status: FindingStatus = FindingStatus.CANDIDATE
    confidence: float = 0.5
    evidence: list[Evidence] = field(default_factory=list)
    frameworks: dict[str, list[str]] = field(default_factory=dict)


@dataclass(frozen=True)
class Target:
    name: str
    base_url: str
    kind: str = "http"
    metadata: dict[str, Any] = field(default_factory=dict)


class ScopeGuard(Protocol):
    def check_url(self, url: str) -> None: ...


@dataclass
class ScanContext:
    target: Target
    scope_guard: ScopeGuard | None = None
    options: dict[str, Any] = field(default_factory=dict)
    profile: ScanProfile = ScanProfile.QUICK

    def check_url(self, url: str) -> None:
        if self.scope_guard:
            self.scope_guard.check_url(url)


class Scanner(Protocol):
    id: str

    async def scan(self, context: ScanContext) -> list[Finding]: ...
