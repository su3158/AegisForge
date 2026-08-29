from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import JSON, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from .db import Base
from .ids import new_id


class Row(Base):
    __abstract__ = True

    # Public IDs are UUID strings so URLs do not leak row counts.
    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=new_id)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    data: Mapped[dict[str, object]] = mapped_column(JSON, default=dict)


class User(Row):
    __tablename__ = "users"


class Project(Row):
    __tablename__ = "projects"


class Target(Row):
    __tablename__ = "targets"


class TargetAsset(Row):
    __tablename__ = "target_assets"


class AuthProfile(Row):
    __tablename__ = "auth_profiles"


class ScopeProfile(Row):
    __tablename__ = "scope_profiles"


class Scan(Row):
    __tablename__ = "scans"


class ScanProfile(Row):
    __tablename__ = "scan_profiles"


class ScanJob(Row):
    __tablename__ = "scan_jobs"


class ScanExecution(Row):
    __tablename__ = "scan_executions"


class Plugin(Row):
    __tablename__ = "plugins"


class PluginRun(Row):
    __tablename__ = "plugin_runs"


class Finding(Row):
    __tablename__ = "findings"


class FindingFramework(Row):
    __tablename__ = "finding_frameworks"


class FindingStatusHistory(Row):
    __tablename__ = "finding_status_history"


class Evidence(Row):
    __tablename__ = "evidence"


class AttackChain(Row):
    __tablename__ = "attack_chains"


class AttackChainNode(Row):
    __tablename__ = "attack_chain_nodes"


class AttackChainEdge(Row):
    __tablename__ = "attack_chain_edges"


class Framework(Row):
    __tablename__ = "frameworks"


class FrameworkControl(Row):
    __tablename__ = "framework_controls"


class ControlResult(Row):
    __tablename__ = "control_results"


class AIProvider(Row):
    __tablename__ = "ai_providers"


class AICall(Row):
    __tablename__ = "ai_calls"


class Report(Row):
    __tablename__ = "reports"


class AuditLog(Row):
    __tablename__ = "audit_logs"
