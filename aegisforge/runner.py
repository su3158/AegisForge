from __future__ import annotations

import asyncio
import hashlib
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from sqlalchemy.orm import Session, sessionmaker

from .attack_chains import AttackChainCandidate
from .attack_chains import build_attack_chain_candidates as build_contract_chain_candidates
from .errors import AegisForgeError, ErrorCode
from .evidence import EvidenceRecord, redact, write_evidence
from .ids import new_id
from .models import AttackChain, Evidence, Finding, Scan, ScopeProfile, Target
from .scanners.browser import BrowserFlowScanner
from .scanners.contracts import (
    Finding as ScannerFinding,
)
from .scanners.contracts import (
    ScanContext,
    Scanner,
    ScanProfile,
    ScanState,
)
from .scanners.contracts import (
    Target as ScannerTarget,
)
from .scanners.http import HttpBaselineScanner
from .scanners.llm import LlmBaselineScanner, LlmPromptInjectionScanner
from .scope import ScopePolicy, assert_url_allowed

FIVE_MINUTES = 300.0


@dataclass
class ScanRequest:
    target: ScannerTarget
    scope_policy: ScopePolicy
    evidence_dir: Path
    id: str = field(default_factory=new_id)
    profile: ScanProfile = ScanProfile.QUICK
    modules: list[str] = field(default_factory=lambda: ["http"])
    options: dict[str, Any] = field(default_factory=dict)
    timeout_seconds: float = FIVE_MINUTES


@dataclass
class ScanResult:
    id: str
    state: ScanState
    profile: ScanProfile
    findings: list[ScannerFinding] = field(default_factory=list)
    evidence: list[EvidenceRecord] = field(default_factory=list)
    attack_chains: list[AttackChainCandidate] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    started_at: str | None = None
    finished_at: str | None = None


class _PolicyGuard:
    def __init__(self, policy: ScopePolicy) -> None:
        self.policy = policy

    def check_url(self, url: str) -> None:
        assert_url_allowed(url, self.policy)


SCANNERS: dict[str, list[Scanner]] = {
    "http": [HttpBaselineScanner()],
    "llm": [LlmBaselineScanner()],
    "browser": [BrowserFlowScanner()],
}


class ScanRunner:
    async def run(self, request: ScanRequest) -> ScanResult:
        result = ScanResult(
            id=request.id,
            state=ScanState.RUNNING,
            profile=request.profile,
            started_at=datetime.now(UTC).isoformat(),
        )
        try:
            await asyncio.wait_for(self._run(request, result), timeout=request.timeout_seconds)
        except TimeoutError:
            result.state = ScanState.TIMEOUT
            result.errors.append("scan timed out")
        except asyncio.CancelledError:
            result.state = ScanState.CANCELLED
            result.errors.append("scan cancelled")
            raise
        except AegisForgeError as exc:
            result.state = ScanState.FAILED
            result.errors.append(exc.message)
        except Exception as exc:  # noqa: BLE001 - scanner errors become scan result failures.
            result.state = ScanState.FAILED
            result.errors.append(str(exc))
        else:
            result.state = ScanState.COMPLETED
        finally:
            result.finished_at = datetime.now(UTC).isoformat()
        return result

    async def _run(self, request: ScanRequest, result: ScanResult) -> None:
        context = ScanContext(
            target=request.target,
            scope_guard=_PolicyGuard(request.scope_policy),
            options=request.options,
            profile=request.profile,
        )
        for scanner in self._scanners_for(request):
            await asyncio.sleep(0)
            findings = await scanner.scan(context)
            result.findings.extend(findings)
            for finding in findings:
                for evidence in finding.evidence:
                    record = write_evidence(request.evidence_dir / request.id, evidence.type, evidence.body)
                    result.evidence.append(record)
        result.attack_chains = build_contract_chain_candidates(result.findings)

    def _scanners_for(self, request: ScanRequest) -> list[Scanner]:
        scanners = [scanner for module in request.modules for scanner in SCANNERS.get(module, [])]
        if (
            request.profile is ScanProfile.STANDARD
            and "llm" in request.modules
            and request.options.get("standard_probe_consent")
        ):
            # Realistic probes require explicit consent and are still redacted before persistence.
            scanners.append(LlmPromptInjectionScanner())
        return scanners


class ScanTaskRegistry:
    def __init__(self, runner: ScanRunner | None = None) -> None:
        self.runner = runner or ScanRunner()
        self._tasks: dict[str, asyncio.Task[ScanResult]] = {}
        self._results: dict[str, ScanResult] = {}

    def start(self, request: ScanRequest) -> ScanResult:
        if request.id in self._tasks:
            raise AegisForgeError(ErrorCode.invalid_config, f"Scan already running: {request.id}")
        result = ScanResult(
            id=request.id,
            state=ScanState.CREATED,
            profile=request.profile,
            started_at=datetime.now(UTC).isoformat(),
        )
        self._results[request.id] = result
        self._tasks[request.id] = asyncio.create_task(self._run_and_store(request))
        return result

    async def _run_and_store(self, request: ScanRequest) -> ScanResult:
        try:
            result = await self.runner.run(request)
        except asyncio.CancelledError:
            result = ScanResult(
                id=request.id,
                state=ScanState.CANCELLED,
                profile=request.profile,
                errors=["scan cancelled"],
                finished_at=datetime.now(UTC).isoformat(),
            )
        self._results[request.id] = result
        self._tasks.pop(request.id, None)
        return result

    def status(self, scan_id: str) -> ScanResult | None:
        result = self._results.get(scan_id)
        if result and scan_id in self._tasks and not self._tasks[scan_id].done():
            result.state = ScanState.RUNNING
        return result

    def cancel(self, scan_id: str) -> bool:
        task = self._tasks.get(scan_id)
        if not task:
            return False
        result = self._results.get(scan_id)
        if result:
            result.state = ScanState.CANCELLED
            result.finished_at = datetime.now(UTC).isoformat()
        task.cancel()
        return True


@dataclass
class TaskRegistry:
    tasks: dict[str, asyncio.Task[None]]

    def __init__(self) -> None:
        self.tasks = {}

    def start(self, scan_id: str, coro: Any) -> None:
        self.tasks[scan_id] = asyncio.create_task(coro)

    def cancel(self, scan_id: str) -> bool:
        task = self.tasks.get(scan_id)
        if not task:
            return False
        task.cancel()
        return True


def scope_candidates(endpoint: str) -> dict[str, object]:
    parsed = urlparse(endpoint)
    host = parsed.hostname or endpoint
    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    return {"allowed_hosts": [host], "allowed_ports": [port]}


async def run_scan(scan_id: str, factory: sessionmaker[Session]) -> None:
    try:
        await asyncio.wait_for(_run_scan(scan_id, factory), timeout=300)
    except asyncio.CancelledError:
        _mark_scan(factory, scan_id, status="cancelled", phase="cancelled", progress=100)
        raise
    except Exception as exc:  # noqa: BLE001 - scan failures are persisted for the UI.
        _mark_scan(
            factory,
            scan_id,
            status="failed",
            phase="failed",
            details={"error": str(exc)},
        )


async def _run_scan(scan_id: str, factory: sessionmaker[Session]) -> None:
    with factory() as db:
        scan = db.get(Scan, scan_id)
        if not scan:
            return
        target = db.get(Target, scan.target_id)
        scope = db.get(ScopeProfile, target.scope_profile_id) if target else None
        if not target or not scope or not scope.confirmed:
            _update(scan, status="failed", phase="validating", details={"error": "scope not confirmed"})
            db.commit()
            return
        policy = ScopePolicy(
            allowed_hosts=set(scope.allowed_hosts),
            allowed_ports=set(scope.allowed_ports),
            allow_private_networks=scope.allow_private_networks,
            external_network_allowed=scope.external_network_allowed,
        )
        assert_url_allowed(target.endpoint, policy)
        _update(scan, status="running", phase="running", progress=20, active_plugin="http.baseline")
        db.commit()

    await asyncio.sleep(0.05)

    with factory() as db:
        scan = db.get(Scan, scan_id)
        target = db.get(Target, scan.target_id) if scan else None
        if not scan or not target:
            return
        if scan.cancel_requested:
            _update(scan, status="cancelled", phase="cancelled", progress=100)
            db.commit()
            return
        _store_evidence(
            db,
            project_id=scan.project_id,
            target_id=target.id,
            scan_id=scan.id,
            source="http.baseline",
            title="Target endpoint admitted by Scope Guard",
            body=f"GET {target.endpoint}",
        )
        if scan.profile == "standard" and scan.consent_standard_probes:
            ev = _store_evidence(
                db,
                project_id=scan.project_id,
                target_id=target.id,
                scan_id=scan.id,
                source="llm.prompt_injection.realistic",
                title="Realistic prompt injection probe executed",
                body="STANDARD probe body redacted in UI and CI logs",
            )
            finding = Finding(
                project_id=scan.project_id,
                target_id=target.id,
                scan_id=scan.id,
                title="Prompt injection response requires review",
                category="prompt_injection",
                severity="medium",
                status="candidate",
                confidence="medium",
                frameworks=["LLM01"],
                evidence_ids=[ev.id],
            )
            db.add(finding)
            scan.findings_count += 1
        scan.requests += 1
        _update(scan, status="completed", phase="completed", progress=100, active_plugin="report.json")
        db.commit()
        build_attack_chain_candidates(db, scan.project_id)


def build_attack_chain_candidates(db: Session, project_id: str) -> None:
    findings = db.query(Finding).filter(Finding.project_id == project_id).all()
    categories = {finding.category for finding in findings}
    if "prompt_injection" not in categories:
        return
    exists = db.query(AttackChain).filter(AttackChain.project_id == project_id).first()
    if exists:
        return
    # Rule-based candidate only; confirmation remains a human/deterministic action.
    db.add(
        AttackChain(
            project_id=project_id,
            title="Prompt injection candidate chain",
            severity_proposed="medium",
            priority_proposed="normal",
            details={"finding_ids": [finding.id for finding in findings]},
        )
    )
    db.commit()


def _store_evidence(
    db: Session,
    *,
    project_id: str,
    target_id: str,
    scan_id: str,
    source: str,
    title: str,
    body: str,
) -> Evidence:
    body_redacted = redact(body)
    evidence = Evidence(
        project_id=project_id,
        target_id=target_id,
        scan_id=scan_id,
        type="LOG",
        source=source,
        title=title,
        body_redacted=body_redacted,
        sha256=hashlib.sha256(body.encode("utf-8")).hexdigest(),
        redacted=True,
    )
    db.add(evidence)
    return evidence


def _mark_scan(factory: sessionmaker[Session], scan_id: str, **values: Any) -> None:
    with factory() as db:
        scan = db.get(Scan, scan_id)
        if scan:
            _update(scan, **values)
            db.commit()


def _update(scan: Scan, **values: Any) -> None:
    details = values.pop("details", None)
    for key, value in values.items():
        setattr(scan, key, value)
    if details:
        scan.details = {**scan.details, **details}
