from __future__ import annotations

import asyncio
from pathlib import Path

import pytest

from aegisforge.attack_chains import build_attack_chain_candidates
from aegisforge.errors import AegisForgeError
from aegisforge.frameworks import load_asvs_l2_controls
from aegisforge.runner import ScanRequest, ScanRunner, ScanTaskRegistry
from aegisforge.scanners.browser import BrowserFlowScanner
from aegisforge.scanners.contracts import (
    Evidence,
    Finding,
    FindingStatus,
    ScanContext,
    ScanProfile,
    ScanState,
    Severity,
    Target,
)
from aegisforge.scope import ScopePolicy, assert_url_allowed


def local_policy() -> ScopePolicy:
    return ScopePolicy(
        allowed_hosts={"127.0.0.1", "example.test"},
        allowed_ports={80, 443, 8000},
        allow_private_networks=True,
    )


class GuardHelper:
    def __init__(self, policy: ScopePolicy) -> None:
        self.policy = policy

    def check_url(self, url: str) -> None:
        assert_url_allowed(url, self.policy)


@pytest.mark.asyncio
async def test_scan_registry_force_cancel(tmp_path: Path) -> None:
    class SlowRunner(ScanRunner):
        async def run(self, request: ScanRequest):  # type: ignore[no-untyped-def]
            await asyncio.sleep(60)

    registry = ScanTaskRegistry(SlowRunner())
    request = ScanRequest(
        target=Target("demo", "http://127.0.0.1:8000"),
        scope_policy=local_policy(),
        evidence_dir=tmp_path,
    )

    registry.start(request)
    assert registry.cancel(request.id)
    await asyncio.sleep(0.01)

    assert registry.status(request.id).state is ScanState.CANCELLED  # type: ignore[union-attr]


@pytest.mark.asyncio
async def test_browser_flow_checks_scope_for_every_goto(tmp_path: Path) -> None:
    flow = tmp_path / "flow.yaml"
    flow.write_text(
        """
steps:
  - action: goto
    url: https://outside.example/
""",
        encoding="utf-8",
    )
    context = ScanContext(
        Target("demo", "http://127.0.0.1:8000"),
        scope_guard=GuardHelper(local_policy()),
        options={"flow": str(flow)},
    )

    with pytest.raises(AegisForgeError):
        await BrowserFlowScanner().scan(context)


@pytest.mark.asyncio
async def test_runner_normalizes_redacted_evidence(tmp_path: Path) -> None:
    class TokenScanner:
        id = "test.token"

        async def scan(self, context: ScanContext) -> list[Finding]:
            return [
                Finding(
                    "Token evidence",
                    "llm_reachability",
                    Severity.INFO,
                    FindingStatus.CANDIDATE,
                    evidence=[Evidence("PROMPT", "Authorization: Bearer secret-token", self.id)],
                )
            ]

    class OneScannerRunner(ScanRunner):
        def _scanners_for(self, request: ScanRequest):  # type: ignore[no-untyped-def]
            return [TokenScanner()]

    result = await OneScannerRunner().run(
        ScanRequest(
            target=Target("demo", "http://127.0.0.1:8000"),
            scope_policy=local_policy(),
            evidence_dir=tmp_path,
        )
    )

    assert result.state is ScanState.COMPLETED
    assert result.evidence
    assert "secret-token" not in Path(result.evidence[0].path).read_text(encoding="utf-8")


def test_attack_chain_rule_candidates() -> None:
    findings = [
        Finding("LLM", "llm_reachability"),
        Finding("Injection", "prompt_injection"),
        Finding("Tool", "tool_misuse"),
    ]

    candidates = build_attack_chain_candidates(findings)

    assert candidates[0].title == "Prompt injection to tool misuse"


def test_asvs_l2_inventory_defaults_not_tested() -> None:
    controls = load_asvs_l2_controls()

    assert controls
    assert {control.status for control in controls} == {"NOT_TESTED"}
    assert all(control.level in {1, 2} for control in controls)


@pytest.mark.asyncio
async def test_standard_profile_requires_consent_for_realistic_probe(tmp_path: Path) -> None:
    scanners = ScanRunner()._scanners_for(
        ScanRequest(
            target=Target("demo", "http://127.0.0.1:8000"),
            scope_policy=local_policy(),
            evidence_dir=tmp_path,
            profile=ScanProfile.STANDARD,
            modules=["llm"],
        )
    )

    assert [scanner.id for scanner in scanners] == ["llm.baseline"]
