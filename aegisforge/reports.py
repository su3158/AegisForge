from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class Finding:
    id: str
    title: str
    category: str
    plugin_id: str | None = None
    status: str = "CANDIDATE"
    severity: str = "INFO"
    confidence: str = "LOW"
    evidence: list[str] = field(default_factory=list)
    frameworks: dict[str, list[str]] = field(default_factory=dict)


def render_json(findings: list[Finding]) -> str:
    return json.dumps({"findings": [asdict(f) for f in findings]}, indent=2)


def render_markdown(findings: list[Finding]) -> str:
    lines = ["# AegisForge Report", ""]
    for finding in findings:
        lines += [
            f"## {finding.id}: {finding.title}",
            "",
            f"- Status: {finding.status}",
            f"- Severity: {finding.severity}",
            f"- Confidence: {finding.confidence}",
            f"- Category: {finding.category}",
            "",
        ]
    return "\n".join(lines)


def render_html(findings: list[Finding]) -> str:
    body = "".join(
        f"<article><h2>{f.id}: {f.title}</h2><p>{f.status} / {f.severity} / {f.confidence}</p></article>"
        for f in findings
    )
    return f"<!doctype html><html><head><title>AegisForge Report</title></head><body><h1>AegisForge Report</h1>{body}</body></html>"


def render_sarif(findings: list[Finding]) -> str:
    rules: dict[str, dict[str, Any]] = {}
    results = []
    for finding in findings:
        rule_id = finding.plugin_id or finding.category
        rules.setdefault(rule_id, {"id": rule_id, "name": finding.title, "properties": finding.frameworks})
        results.append(
            {
                "ruleId": rule_id,
                "level": "error" if finding.severity in {"HIGH", "CRITICAL"} else "warning",
                "message": {"text": finding.title},
                "properties": {"finding_id": finding.id, "status": finding.status},
            }
        )
    return json.dumps(
        {
            "version": "2.1.0",
            "$schema": "https://json.schemastore.org/sarif-2.1.0.json",
            "runs": [{"tool": {"driver": {"name": "AegisForge", "rules": list(rules.values())}}, "results": results}],
        },
        indent=2,
    )
