from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .contracts import Evidence, Finding, ScanContext, Severity


def browser_flow_candidate(name: str, start_url: str, prompt_selector: str = "textarea") -> dict[str, Any]:
    return {
        "name": name,
        "start_url": start_url,
        "steps": [
            {"action": "goto", "url": start_url},
            {"action": "fill", "selector": prompt_selector, "value": "{{prompt}}"},
            {"action": "press", "selector": prompt_selector, "key": "Enter"},
        ],
    }


def write_candidate(path: str | Path, candidate: dict[str, Any]) -> None:
    Path(path).write_text(_dump_yaml(candidate), encoding="utf-8")


class BrowserFlowScanner:
    id = "browser.flow"

    async def scan(self, context: ScanContext) -> list[Finding]:
        flow_path = context.options.get("flow")
        if not flow_path:
            candidate = browser_flow_candidate(context.target.name, context.target.base_url)
            evidence = Evidence("CONFIGURATION", json.dumps(candidate, indent=2), self.id)
            return [Finding("Browser flow candidate generated", "browser_flow", Severity.INFO, evidence=[evidence])]
        context.check_url(context.target.base_url)
        evidence = Evidence("CONFIGURATION", Path(flow_path).read_text(encoding="utf-8"), self.id)
        return [Finding("Browser flow loaded for execution", "browser_flow", Severity.INFO, evidence=[evidence])]


def _dump_yaml(value: Any, indent: int = 0) -> str:
    if isinstance(value, dict):
        return "".join(f"{' ' * indent}{k}: {_dump_yaml(v, indent + 2) if isinstance(v, (dict, list)) else _scalar(v)}\n" for k, v in value.items())
    if isinstance(value, list):
        return "".join(f"{' ' * indent}- {_dump_yaml(v, indent + 2).lstrip() if isinstance(v, (dict, list)) else _scalar(v)}\n" for v in value)
    return _scalar(value)


def _scalar(value: Any) -> str:
    return json.dumps(value) if isinstance(value, str) else str(value).lower()

