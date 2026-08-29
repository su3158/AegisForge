from __future__ import annotations

import json
import subprocess
from pathlib import Path

from aegisforge.scanners.contracts import Evidence, Finding, Severity


def load_garak_result(path: str | Path) -> list[Finding]:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    records = raw if isinstance(raw, list) else raw.get("results", [])
    findings: list[Finding] = []
    for record in records:
        evidence = Evidence("EXTERNAL_SCANNER_RESULT", json.dumps(record, sort_keys=True), "garak")
        findings.append(
            Finding(
                title=f"garak: {record.get('probe', 'external result')}",
                category="llm_external",
                severity=Severity(record.get("severity", "info")) if record.get("severity") in Severity else Severity.INFO,
                confidence=float(record.get("score", 0.5)),
                evidence=[evidence],
            )
        )
    return findings


def run_garak(args: list[str], output: str | Path) -> list[Finding]:
    subprocess.run(["garak", *args], check=True)
    return load_garak_result(output)
