from __future__ import annotations

from enum import Enum, IntEnum


class ErrorCode(str, Enum):
    ok = "ok"
    internal_error = "internal_error"
    invalid_config = "invalid_config"
    scope_violation = "scope_violation"
    threshold_exceeded = "threshold_exceeded"
    target_unavailable = "target_unavailable"
    scan_cancelled = "scan_cancelled"


EXIT_CODES = {
    ErrorCode.ok: 0,
    ErrorCode.internal_error: 1,
    ErrorCode.invalid_config: 2,
    ErrorCode.scope_violation: 3,
    ErrorCode.threshold_exceeded: 4,
    ErrorCode.target_unavailable: 5,
    ErrorCode.scan_cancelled: 6,
}


class ExitCode(IntEnum):
    OK = 0
    INTERNAL_ERROR = 1
    INVALID_CONFIG = 2
    SCOPE_VIOLATION = 3
    THRESHOLD_EXCEEDED = 4
    TARGET_UNAVAILABLE = 5
    SCAN_CANCELLED = 6


class AegisForgeError(Exception):
    def __init__(self, code: ErrorCode, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message

    @property
    def exit_code(self) -> int:
        return EXIT_CODES[self.code]
