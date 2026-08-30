from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .db import Base
from .ids import new_id


def now() -> datetime:
    return datetime.now(UTC)


class Row(Base):
    __abstract__ = True

    # Public IDs are non-sequential so exposed URLs do not leak row counts.
    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=new_id)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, onupdate=now)


class Project(Row):
    __tablename__ = "projects"

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    owner: Mapped[str] = mapped_column(String(120), default="")
    risk: Mapped[str] = mapped_column(String(20), default="medium")
    details: Mapped[dict[str, object]] = mapped_column(JSON, default=dict)


class ScopeProfile(Row):
    __tablename__ = "scope_profiles"

    project_id: Mapped[str] = mapped_column(String(64), ForeignKey("projects.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(120), default="default")
    allowed_hosts: Mapped[list[str]] = mapped_column(JSON, default=list)
    allowed_ports: Mapped[list[int]] = mapped_column(JSON, default=lambda: [80, 443])
    allow_private_networks: Mapped[bool] = mapped_column(Boolean, default=False)
    external_network_allowed: Mapped[bool] = mapped_column(Boolean, default=False)
    confirmed: Mapped[bool] = mapped_column(Boolean, default=False)


class Target(Row):
    __tablename__ = "targets"

    project_id: Mapped[str] = mapped_column(String(64), ForeignKey("projects.id"), nullable=False)
    scope_profile_id: Mapped[str | None] = mapped_column(String(64), ForeignKey("scope_profiles.id"))
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    kind: Mapped[str] = mapped_column(String(30), default="web")
    endpoint: Mapped[str] = mapped_column(String(1000), nullable=False)
    health: Mapped[str] = mapped_column(String(30), default="unknown")
    details: Mapped[dict[str, object]] = mapped_column(JSON, default=dict)


class Secret(Row):
    __tablename__ = "secrets"

    name: Mapped[str] = mapped_column(String(200), unique=True, nullable=False)
    scope: Mapped[str] = mapped_column(String(30), default="app")
    ciphertext: Mapped[str] = mapped_column(Text, nullable=False)
    details: Mapped[dict[str, object]] = mapped_column(JSON, default=dict)


class Scan(Row):
    __tablename__ = "scans"

    project_id: Mapped[str] = mapped_column(String(64), ForeignKey("projects.id"), nullable=False)
    target_id: Mapped[str] = mapped_column(String(64), ForeignKey("targets.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    profile: Mapped[str] = mapped_column(String(30), default="quick")
    safety: Mapped[str] = mapped_column(String(30), default="safe")
    status: Mapped[str] = mapped_column(String(30), default="created")
    phase: Mapped[str] = mapped_column(String(30), default="created")
    progress: Mapped[int] = mapped_column(Integer, default=0)
    active_plugin: Mapped[str] = mapped_column(String(200), default="")
    requests: Mapped[int] = mapped_column(Integer, default=0)
    ai_cost_usd: Mapped[float] = mapped_column(Float, default=0.0)
    findings_count: Mapped[int] = mapped_column(Integer, default=0)
    cancel_requested: Mapped[bool] = mapped_column(Boolean, default=False)
    consent_standard_probes: Mapped[bool] = mapped_column(Boolean, default=False)
    details: Mapped[dict[str, object]] = mapped_column(JSON, default=dict)


class ScanExecution(Row):
    __tablename__ = "scan_executions"

    scan_id: Mapped[str] = mapped_column(String(64), ForeignKey("scans.id"), nullable=False)
    plugin_id: Mapped[str] = mapped_column(String(200), nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="created")
    details: Mapped[dict[str, object]] = mapped_column(JSON, default=dict)


class Finding(Row):
    __tablename__ = "findings"

    project_id: Mapped[str] = mapped_column(String(64), ForeignKey("projects.id"), nullable=False)
    target_id: Mapped[str] = mapped_column(String(64), ForeignKey("targets.id"), nullable=False)
    scan_id: Mapped[str | None] = mapped_column(String(64), ForeignKey("scans.id"))
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    category: Mapped[str] = mapped_column(String(120), nullable=False)
    severity: Mapped[str] = mapped_column(String(20), default="info")
    status: Mapped[str] = mapped_column(String(30), default="candidate")
    confidence: Mapped[str] = mapped_column(String(30), default="medium")
    frameworks: Mapped[list[str]] = mapped_column(JSON, default=list)
    evidence_ids: Mapped[list[str]] = mapped_column(JSON, default=list)
    details: Mapped[dict[str, object]] = mapped_column(JSON, default=dict)


class Evidence(Row):
    __tablename__ = "evidence"

    project_id: Mapped[str] = mapped_column(String(64), ForeignKey("projects.id"), nullable=False)
    target_id: Mapped[str | None] = mapped_column(String(64), ForeignKey("targets.id"))
    scan_id: Mapped[str | None] = mapped_column(String(64), ForeignKey("scans.id"))
    execution_id: Mapped[str | None] = mapped_column(String(64), ForeignKey("scan_executions.id"))
    type: Mapped[str] = mapped_column(String(50), nullable=False)
    source: Mapped[str] = mapped_column(String(200), nullable=False)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    body_redacted: Mapped[str] = mapped_column(Text, default="")
    body_ciphertext: Mapped[str | None] = mapped_column(Text)
    sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    redacted: Mapped[bool] = mapped_column(Boolean, default=True)
    details: Mapped[dict[str, object]] = mapped_column(JSON, default=dict)


class AttackChain(Row):
    __tablename__ = "attack_chains"

    project_id: Mapped[str] = mapped_column(String(64), ForeignKey("projects.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="candidate")
    severity_proposed: Mapped[str] = mapped_column(String(20), default="info")
    priority_proposed: Mapped[str] = mapped_column(String(20), default="normal")
    details: Mapped[dict[str, object]] = mapped_column(JSON, default=dict)


class FrameworkControl(Row):
    __tablename__ = "framework_controls"

    framework: Mapped[str] = mapped_column(String(120), nullable=False)
    version: Mapped[str] = mapped_column(String(50), nullable=False)
    control_id: Mapped[str] = mapped_column(String(120), nullable=False)
    level: Mapped[str] = mapped_column(String(20), default="L2")
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="not_tested")
    details: Mapped[dict[str, object]] = mapped_column(JSON, default=dict)


class Report(Row):
    __tablename__ = "reports"

    project_id: Mapped[str] = mapped_column(String(64), ForeignKey("projects.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    format: Mapped[str] = mapped_column(String(30), default="json")
    body: Mapped[str] = mapped_column(Text, default="")
    details: Mapped[dict[str, object]] = mapped_column(JSON, default=dict)


class AuditLog(Row):
    __tablename__ = "audit_logs"

    event: Mapped[str] = mapped_column(String(120), nullable=False)
    actor: Mapped[str] = mapped_column(String(120), default="system")
    project_id: Mapped[str | None] = mapped_column(String(64), ForeignKey("projects.id"))
    details: Mapped[dict[str, object]] = mapped_column(JSON, default=dict)
