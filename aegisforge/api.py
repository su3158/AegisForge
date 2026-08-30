from __future__ import annotations

import hmac
import secrets as py_secrets
from hashlib import sha256
from pathlib import Path
from typing import Any

from fastapi import Depends, FastAPI, Header, HTTPException, Request, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from . import __version__
from .config import Settings, load_settings
from .db import Base, reset_legacy_alpha_schema, session_factory
from .models import (
    AttackChain,
    AuditLog,
    Evidence,
    Finding,
    FrameworkControl,
    Project,
    Report,
    Scan,
    ScopeProfile,
    Secret,
    Target,
)
from .runner import TaskRegistry, run_scan, scope_candidates
from .secrets import decrypt_secret, encrypt_secret

SESSION_COOKIE = "aegisforge_session"
CSRF_COOKIE = "aegisforge_csrf"


class ProjectIn(BaseModel):
    name: str
    owner: str = ""
    risk: str = "medium"
    details: dict[str, object] = Field(default_factory=dict)


class TargetIn(BaseModel):
    project_id: str
    name: str
    kind: str = "web"
    endpoint: str | None = None
    base_url: str | None = None
    scope_profile_id: str | None = None
    details: dict[str, object] = Field(default_factory=dict)


class ScopeIn(BaseModel):
    project_id: str
    name: str = "default"
    allowed_hosts: list[str] = Field(default_factory=list)
    allowed_ports: list[int] = Field(default_factory=lambda: [80, 443])
    allow_private_networks: bool = False
    external_network_allowed: bool = False
    confirmed: bool = False


class ScanIn(BaseModel):
    project_id: str
    target_id: str
    name: str = "Quick scan"
    profile: str = "quick"
    safety: str = "safe"
    consent_standard_probes: bool = False
    details: dict[str, object] = Field(default_factory=dict)


class SecretIn(BaseModel):
    name: str
    value: str
    scope: str = "app"


class LoginIn(BaseModel):
    password: str


class RawRevealIn(BaseModel):
    password: str


class EvidenceIn(BaseModel):
    project_id: str
    target_id: str | None = None
    scan_id: str | None = None
    evidence_type: str = "LOG"
    body: str
    raw_body: str | None = None
    title: str = "Manual evidence"
    source: str = "api.manual"


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or load_settings()
    factory = session_factory(settings.database_url)
    engine = factory.kw["bind"]
    reset_legacy_alpha_schema(engine, Base)
    Base.metadata.create_all(engine)
    registry = TaskRegistry()
    app = FastAPI(title="AegisForge", version=__version__)
    seed_frameworks(factory)

    def get_db() -> Any:
        with factory() as session:
            yield session

    def auth_required() -> bool:
        return bool(settings.admin_password) or settings.host not in {
            "127.0.0.1",
            "localhost",
        } or settings.database_url.startswith("postgresql")

    def check_session(request: Request) -> None:
        if not auth_required():
            return
        cookie = request.cookies.get(SESSION_COOKIE)
        if not cookie or not _verify_session(cookie, settings.secret_key):
            raise HTTPException(status_code=401, detail="authentication required")

    def check_write(request: Request, x_csrf_token: str | None = Header(default=None)) -> None:
        check_session(request)
        if not auth_required():
            return
        # Double-submit token: cross-site forms cannot set the custom header.
        if not x_csrf_token or x_csrf_token != request.cookies.get(CSRF_COOKIE):
            raise HTTPException(status_code=403, detail="csrf token required")

    @app.get("/api/v1/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "version": __version__}

    @app.post("/api/v1/auth/login")
    def login(payload: LoginIn, response: Response) -> dict[str, str]:
        if settings.admin_password and not hmac.compare_digest(payload.password, settings.admin_password):
            raise HTTPException(status_code=401, detail="invalid credentials")
        if auth_required() and not settings.admin_password:
            raise HTTPException(status_code=500, detail="admin password required")
        csrf = py_secrets.token_urlsafe(24)
        response.set_cookie(
            SESSION_COOKIE,
            _sign_session(settings.secret_key),
            httponly=True,
            samesite="lax",
        )
        response.set_cookie(CSRF_COOKIE, csrf, httponly=False, samesite="lax")
        return {"csrf_token": csrf}

    @app.post("/api/v1/auth/logout")
    def logout(response: Response) -> dict[str, str]:
        response.delete_cookie(SESSION_COOKIE)
        response.delete_cookie(CSRF_COOKIE)
        return {"status": "ok"}

    @app.get("/api/v1/auth/session")
    def session(request: Request) -> dict[str, object]:
        return {
            "auth_required": auth_required(),
            "authenticated": bool(request.cookies.get(SESSION_COOKIE)),
            "csrf_token": request.cookies.get(CSRF_COOKIE),
        }

    @app.get("/api/v1/settings")
    def read_settings() -> dict[str, str | bool]:
        backend = "postgres" if settings.database_url.startswith("postgresql") else "sqlite"
        return {"database": backend, "offline": settings.offline, "auth_required": auth_required()}

    @app.get("/api/v1/console")
    def console(db: Session = Depends(get_db)) -> dict[str, list[dict[str, Any]]]:
        return {
            "projects": [_project(row, db) for row in db.query(Project).all()],
            "targets": [_target(row, db) for row in db.query(Target).all()],
            "scans": [_scan(row) for row in db.query(Scan).all()],
            "findings": [_finding(row) for row in db.query(Finding).all()],
            "evidence": [_evidence(row) for row in db.query(Evidence).all()],
            "chains": [_chain(row) for row in db.query(AttackChain).all()],
            "coverage": [_control(row) for row in db.query(FrameworkControl).all()],
        }

    @app.get("/api/v1/projects")
    def list_projects(db: Session = Depends(get_db)) -> list[dict[str, Any]]:
        return [_project(row, db) for row in db.query(Project).all()]

    @app.post("/api/v1/projects", dependencies=[Depends(check_write)])
    def create_project(payload: ProjectIn, db: Session = Depends(get_db)) -> dict[str, Any]:
        project = Project(**payload.model_dump())
        db.add(project)
        db.commit()
        return _project(project, db)

    @app.get("/api/v1/targets")
    def list_targets(db: Session = Depends(get_db)) -> list[dict[str, Any]]:
        return [_target(row, db) for row in db.query(Target).all()]

    @app.post("/api/v1/targets", dependencies=[Depends(check_write)])
    def create_target(payload: TargetIn, db: Session = Depends(get_db)) -> dict[str, Any]:
        endpoint = payload.endpoint or payload.base_url
        if not endpoint:
            raise HTTPException(status_code=422, detail="endpoint is required")
        scope_id = payload.scope_profile_id
        if not scope_id:
            candidates = scope_candidates(endpoint)
            scope = ScopeProfile(project_id=payload.project_id, **candidates)
            db.add(scope)
            db.flush()
            scope_id = scope.id
        target = Target(
            project_id=payload.project_id,
            name=payload.name,
            kind=payload.kind,
            endpoint=endpoint,
            scope_profile_id=scope_id,
            details=payload.details,
        )
        db.add(target)
        db.commit()
        return _target(target, db)

    @app.post("/api/v1/scopes", dependencies=[Depends(check_write)])
    def create_scope(payload: ScopeIn, db: Session = Depends(get_db)) -> dict[str, Any]:
        scope = ScopeProfile(**payload.model_dump())
        db.add(scope)
        db.commit()
        return _scope(scope)

    @app.patch("/api/v1/scopes/{scope_id}", dependencies=[Depends(check_write)])
    def update_scope(scope_id: str, payload: ScopeIn, db: Session = Depends(get_db)) -> dict[str, Any]:
        scope = _get(db, ScopeProfile, scope_id)
        for key, value in payload.model_dump().items():
            setattr(scope, key, value)
        db.commit()
        return _scope(scope)

    @app.get("/api/v1/scans")
    def list_scans(db: Session = Depends(get_db)) -> list[dict[str, Any]]:
        return [_scan(row) for row in db.query(Scan).all()]

    @app.post("/api/v1/scans", dependencies=[Depends(check_write)])
    def create_scan(payload: ScanIn, db: Session = Depends(get_db)) -> dict[str, Any]:
        scan = Scan(**payload.model_dump())
        db.add(scan)
        db.commit()
        return _scan(scan)

    @app.get("/api/v1/scans/{scan_id}")
    def read_scan(scan_id: str, db: Session = Depends(get_db)) -> dict[str, Any]:
        return _scan(_get(db, Scan, scan_id))

    @app.post("/api/v1/scans/{scan_id}/start", dependencies=[Depends(check_write)])
    async def start_scan(scan_id: str, db: Session = Depends(get_db)) -> dict[str, Any]:
        scan = _get(db, Scan, scan_id)
        target = _get(db, Target, scan.target_id)
        scope = db.get(ScopeProfile, target.scope_profile_id) if target.scope_profile_id else None
        if not scope or not scope.confirmed:
            raise HTTPException(status_code=400, detail="scope confirmation required")
        scan.status = "running"
        scan.phase = "running"
        db.commit()
        registry.start(scan_id, run_scan(scan_id, factory))
        return _scan(scan)

    @app.post("/api/v1/scans/{scan_id}/cancel", dependencies=[Depends(check_write)])
    def cancel_scan(scan_id: str, db: Session = Depends(get_db)) -> dict[str, Any]:
        scan = _get(db, Scan, scan_id)
        scan.cancel_requested = True
        scan.status = "cancelling"
        registry.cancel(scan_id)
        db.commit()
        return _scan(scan)

    @app.get("/api/v1/findings")
    def list_findings(db: Session = Depends(get_db)) -> list[dict[str, Any]]:
        return [_finding(row) for row in db.query(Finding).all()]

    @app.get("/api/v1/evidence")
    def list_evidence(db: Session = Depends(get_db)) -> list[dict[str, Any]]:
        return [_evidence(row) for row in db.query(Evidence).all()]

    @app.post("/api/v1/evidence", dependencies=[Depends(check_write)])
    def create_evidence(payload: EvidenceIn, db: Session = Depends(get_db)) -> dict[str, Any]:
        import hashlib

        from .evidence import redact

        raw = payload.raw_body or payload.body
        evidence = Evidence(
            project_id=payload.project_id,
            target_id=payload.target_id,
            scan_id=payload.scan_id,
            type=payload.evidence_type,
            source=payload.source,
            title=payload.title,
            body_redacted=redact(payload.body),
            body_ciphertext=encrypt_secret(raw, settings.secret_key) if settings.secret_key else None,
            sha256=hashlib.sha256(raw.encode("utf-8")).hexdigest(),
            redacted=True,
        )
        db.add(evidence)
        db.commit()
        return _evidence(evidence)

    @app.post("/api/v1/evidence/{evidence_id}/raw", dependencies=[Depends(check_write)])
    def reveal_raw(evidence_id: str, payload: RawRevealIn, db: Session = Depends(get_db)) -> dict[str, str]:
        if settings.admin_password and not hmac.compare_digest(payload.password, settings.admin_password):
            raise HTTPException(status_code=401, detail="invalid credentials")
        evidence = _get(db, Evidence, evidence_id)
        if not evidence.body_ciphertext:
            raise HTTPException(status_code=404, detail="raw evidence unavailable")
        db.add(AuditLog(event="raw_evidence_revealed", project_id=evidence.project_id, details={"id": evidence.id}))
        db.commit()
        return {"body": decrypt_secret(evidence.body_ciphertext, settings.secret_key)}

    @app.get("/api/v1/secrets")
    def list_secrets(db: Session = Depends(get_db)) -> list[dict[str, Any]]:
        return [{"id": row.id, "name": row.name, "scope": row.scope} for row in db.query(Secret).all()]

    @app.get("/api/v1/settings/secrets")
    def list_settings_secrets(db: Session = Depends(get_db)) -> list[dict[str, Any]]:
        return list_secrets(db)

    @app.post("/api/v1/secrets", dependencies=[Depends(check_write)])
    def set_secret(payload: SecretIn, db: Session = Depends(get_db)) -> dict[str, str]:
        secret = db.query(Secret).filter(Secret.name == payload.name).first()
        ciphertext = encrypt_secret(payload.value, settings.secret_key)
        if secret:
            secret.ciphertext = ciphertext
            secret.scope = payload.scope
        else:
            secret = Secret(name=payload.name, scope=payload.scope, ciphertext=ciphertext)
            db.add(secret)
        db.add(AuditLog(event="secret_created", details={"name": payload.name, "scope": payload.scope}))
        db.commit()
        return {"status": "ok", "name": payload.name}

    @app.post("/api/v1/settings/secrets", dependencies=[Depends(check_write)])
    def set_settings_secret(payload: SecretIn, db: Session = Depends(get_db)) -> dict[str, str]:
        return set_secret(payload, db)

    @app.delete("/api/v1/secrets/{name}", dependencies=[Depends(check_write)])
    def delete_secret(name: str, db: Session = Depends(get_db)) -> dict[str, str]:
        secret = db.query(Secret).filter(Secret.name == name).first()
        if secret:
            db.delete(secret)
            db.add(AuditLog(event="secret_deleted", details={"name": name}))
            db.commit()
        return {"status": "ok"}

    @app.get("/api/v1/attack-chains")
    def list_chains(db: Session = Depends(get_db)) -> list[dict[str, Any]]:
        return [_chain(row) for row in db.query(AttackChain).all()]

    @app.get("/api/v1/frameworks/coverage")
    def coverage(db: Session = Depends(get_db)) -> list[dict[str, Any]]:
        return [_control(row) for row in db.query(FrameworkControl).all()]

    @app.get("/api/v1/reports")
    def list_reports(db: Session = Depends(get_db)) -> list[dict[str, Any]]:
        return [{"id": row.id, "name": row.name, "format": row.format} for row in db.query(Report).all()]

    @app.get("/api/v1/audit-log")
    def list_audit_log(db: Session = Depends(get_db)) -> list[dict[str, Any]]:
        return [
            {
                "id": row.id,
                "action": row.event,
                "actor": row.actor,
                "projectId": row.project_id,
                "details": row.details,
            }
            for row in db.query(AuditLog).all()
        ]

    web_dist = Path(__file__).resolve().parent.parent / "apps" / "web" / "dist"
    if web_dist.exists():
        app.mount("/", StaticFiles(directory=web_dist, html=True), name="web")

    return app


def seed_frameworks(factory: Any) -> None:
    with factory() as db:
        if db.query(FrameworkControl).first():
            return
        for control_id, title in [
            ("ASVS-5.0.0-V1", "Architecture, Design and Threat Modeling"),
            ("ASVS-5.0.0-V2", "Authentication"),
            ("ASVS-5.0.0-V4", "Access Control"),
            ("ASVS-5.0.0-V5", "Validation, Sanitization and Encoding"),
            ("ASVS-5.0.0-V14", "Configuration"),
        ]:
            db.add(
                FrameworkControl(
                    framework="OWASP ASVS",
                    version="5.0.0",
                    control_id=control_id,
                    title=title,
                    status="not_tested",
                )
            )
        db.commit()


def _sign_session(secret_key: str | None) -> str:
    secret_key = secret_key or "local-dev-only"
    body = "admin"
    sig = hmac.new(secret_key.encode("utf-8"), body.encode("utf-8"), sha256).hexdigest()
    return f"{body}.{sig}"


def _verify_session(cookie: str, secret_key: str | None) -> bool:
    try:
        body, sig = cookie.rsplit(".", 1)
    except ValueError:
        return False
    expected = hmac.new(
        (secret_key or "local-dev-only").encode("utf-8"), body.encode("utf-8"), sha256
    ).hexdigest()
    return hmac.compare_digest(sig, expected)


def _get(db: Session, model: type[Any], item_id: str) -> Any:
    item = db.get(model, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="not found")
    return item


def _project(row: Project, db: Session) -> dict[str, Any]:
    targets = db.query(Target).filter(Target.project_id == row.id).count()
    scans = db.query(Scan).filter(Scan.project_id == row.id).count()
    return {
        "id": row.id,
        "name": row.name,
        "owner": row.owner,
        "risk": row.risk,
        "targets": targets,
        "scans": scans,
        "coverage": 0,
        "lastScan": row.updated_at.isoformat(),
    }


def _target(row: Target, db: Session | None = None) -> dict[str, Any]:
    scope = db.get(ScopeProfile, row.scope_profile_id) if db and row.scope_profile_id else None
    allowed_hosts = scope.allowed_hosts if scope else scope_candidates(row.endpoint)["allowed_hosts"]
    allowed_ports = scope.allowed_ports if scope else scope_candidates(row.endpoint)["allowed_ports"]
    return {
        "id": row.id,
        "projectId": row.project_id,
        "scopeProfileId": row.scope_profile_id,
        "name": row.name,
        "type": row.kind,
        "endpoint": row.endpoint,
        "scope": "safe",
        "health": row.health,
        "allowedHosts": allowed_hosts,
        "allowedPorts": allowed_ports,
        "scopeConfirmed": bool(scope.confirmed) if scope else False,
        "scope_candidates": {"allowed_hosts": allowed_hosts, "allowed_ports": allowed_ports},
    }


def _scope(row: ScopeProfile) -> dict[str, Any]:
    return {
        "id": row.id,
        "projectId": row.project_id,
        "name": row.name,
        "allowedHosts": row.allowed_hosts,
        "allowedPorts": row.allowed_ports,
        "confirmed": row.confirmed,
    }


def _scan(row: Scan) -> dict[str, Any]:
    return {
        "id": row.id,
        "projectId": row.project_id,
        "targetId": row.target_id,
        "name": row.name,
        "profile": row.profile,
        "safety": row.safety,
        "phase": row.phase,
        "status": row.status,
        "progress": row.progress,
        "activePlugin": row.active_plugin,
        "requests": row.requests,
        "aiCostUsd": row.ai_cost_usd,
        "findings": row.findings_count,
        "errors": [row.details["error"]] if "error" in row.details else [],
    }


def _finding(row: Finding) -> dict[str, Any]:
    return {
        "id": row.id,
        "projectId": row.project_id,
        "targetId": row.target_id,
        "title": row.title,
        "severity": row.severity,
        "status": row.status,
        "confidence": row.confidence,
        "category": row.category,
        "target": row.target_id,
        "frameworks": row.frameworks,
        "evidenceIds": row.evidence_ids,
    }


def _evidence(row: Evidence) -> dict[str, Any]:
    return {
        "id": row.id,
        "projectId": row.project_id,
        "type": row.type,
        "title": row.title,
        "timestamp": row.created_at.isoformat(),
        "sha256": row.sha256,
        "redacted": row.redacted,
        "language": row.details.get("language", "text"),
        "after": row.body_redacted,
        "redacted_body": row.body_redacted,
    }


def _chain(row: AttackChain) -> dict[str, Any]:
    return {
        "id": row.id,
        "projectId": row.project_id,
        "title": row.title,
        "status": row.status,
        "severityProposed": row.severity_proposed,
        "priorityProposed": row.priority_proposed,
        "nodes": [
            {"id": "n1", "label": "Prompt injection", "kind": "llm"},
            {"id": "n2", "label": "Review", "kind": "agent"},
        ],
        "edges": [{"from": "n1", "to": "n2", "label": "candidate"}],
    }


def _control(row: FrameworkControl) -> dict[str, Any]:
    return {
        "id": row.control_id,
        "framework": f"{row.framework} {row.version}",
        "title": row.title,
        "status": row.status,
    }
