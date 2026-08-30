from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

from aegisforge.errors import AegisForgeError, ErrorCode

from .contracts import Evidence, Finding, ScanContext, Severity

ALLOWED_ACTIONS = {
    "goto",
    "fill",
    "click",
    "press",
    "wait_for_selector",
    "expect_text",
    "screenshot",
    "select_option",
    "check",
    "uncheck",
}


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
        flow = load_flow(Path(flow_path))
        validate_flow(flow, context)
        evidence = Evidence("CONFIGURATION", json.dumps(flow, indent=2, sort_keys=True), self.id)
        return [Finding("Browser flow validated for execution", "browser_flow", Severity.INFO, evidence=[evidence])]


def load_flow(path: Path) -> dict[str, Any]:
    loaded = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(loaded, dict):
        raise AegisForgeError(ErrorCode.invalid_config, "Browser flow must be a YAML object")
    return loaded


def validate_flow(flow: dict[str, Any], context: ScanContext) -> None:
    steps = flow.get("steps")
    if not isinstance(steps, list):
        raise AegisForgeError(ErrorCode.invalid_config, "Browser flow requires steps")
    for step in steps:
        if not isinstance(step, dict):
            raise AegisForgeError(ErrorCode.invalid_config, "Browser flow step must be an object")
        action = step.get("action")
        if action not in ALLOWED_ACTIONS:
            raise AegisForgeError(ErrorCode.invalid_config, f"Browser flow action is not allowed: {action}")
        # Scope Guard is applied at validation time and must be repeated by real Playwright execution later.
        if action == "goto":
            context.check_url(str(step.get("url", "")))


def _dump_yaml(value: Any, indent: int = 0) -> str:
    if isinstance(value, dict):
        return "".join(f"{' ' * indent}{k}: {_dump_yaml(v, indent + 2) if isinstance(v, (dict, list)) else _scalar(v)}\n" for k, v in value.items())
    if isinstance(value, list):
        return "".join(f"{' ' * indent}- {_dump_yaml(v, indent + 2).lstrip() if isinstance(v, (dict, list)) else _scalar(v)}\n" for v in value)
    return _scalar(value)


def _scalar(value: Any) -> str:
    return json.dumps(value) if isinstance(value, str) else str(value).lower()
