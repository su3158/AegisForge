"""initial v1 table skeleton"""

import sqlalchemy as sa

from alembic import op

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None

TABLES = [
    "users",
    "projects",
    "targets",
    "target_assets",
    "auth_profiles",
    "scope_profiles",
    "scans",
    "scan_profiles",
    "scan_jobs",
    "scan_executions",
    "plugins",
    "plugin_runs",
    "findings",
    "finding_frameworks",
    "finding_status_history",
    "evidence",
    "attack_chains",
    "attack_chain_nodes",
    "attack_chain_edges",
    "frameworks",
    "framework_controls",
    "control_results",
    "ai_providers",
    "ai_calls",
    "reports",
    "audit_logs",
]


def upgrade() -> None:
    for table in TABLES:
        op.create_table(
            table,
            sa.Column("id", sa.String(length=64), primary_key=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("data", sa.JSON(), nullable=False),
        )


def downgrade() -> None:
    for table in reversed(TABLES):
        op.drop_table(table)
