"""AI Research Analyst operationalization.

Revision ID: 0044_ai_research_ops
Revises: 0043_governed_ai_execution
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0044_ai_research_ops"
down_revision: str | None = "0043_governed_ai_execution"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("research_evidence_citations", sa.Column("citation_location", sa.String(500)))
    op.add_column("research_evidence_citations", sa.Column("methodology_version", sa.String(80)))
    op.add_column(
        "research_evidence_citations",
        sa.Column("missing_evidence", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.create_table(
        "research_runs",
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("project_id", sa.Uuid()),
        sa.Column("research_type", sa.String(60), nullable=False),
        sa.Column("objective", sa.Text(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("methodology_version", sa.String(80), nullable=False),
        sa.Column("created_by", sa.Uuid(), nullable=False),
        sa.Column("capability_id", sa.Uuid(), nullable=False),
        sa.Column("prompt_version_id", sa.Uuid()),
        sa.Column("ai_request_id", sa.Uuid()),
        sa.Column("analysis_id", sa.Uuid()),
        sa.Column("decision_queue_item_id", sa.Uuid()),
        sa.Column("started_at", sa.DateTime(timezone=True)),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.Column("failure_reason", sa.Text()),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"]),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["capability_id"], ["ai_model_capabilities.id"]),
        sa.ForeignKeyConstraint(["prompt_version_id"], ["prompt_versions.id"]),
        sa.ForeignKeyConstraint(["ai_request_id"], ["ai_requests.id"]),
        sa.ForeignKeyConstraint(["analysis_id"], ["research_analyses.id"]),
        sa.ForeignKeyConstraint(["decision_queue_item_id"], ["decision_queue_items.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    for column in [
        "organization_id",
        "project_id",
        "created_by",
        "capability_id",
        "prompt_version_id",
        "ai_request_id",
        "analysis_id",
        "decision_queue_item_id",
    ]:
        op.create_index(op.f(f"ix_research_runs_{column}"), "research_runs", [column])
    op.create_table(
        "research_run_evidence",
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("research_run_id", sa.Uuid(), nullable=False),
        sa.Column("evidence_type", sa.String(50), nullable=False),
        sa.Column("evidence_id", sa.Uuid(), nullable=False),
        sa.Column("source_reference", sa.String(500), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.CheckConstraint("confidence BETWEEN 0 AND 1", name="research_run_evidence_confidence"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["research_run_id"], ["research_runs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("research_run_id", "evidence_type", "evidence_id"),
    )
    for column in ["organization_id", "research_run_id", "evidence_id"]:
        op.create_index(
            op.f(f"ix_research_run_evidence_{column}"), "research_run_evidence", [column]
        )


def downgrade() -> None:
    for column in ["evidence_id", "research_run_id", "organization_id"]:
        op.drop_index(
            op.f(f"ix_research_run_evidence_{column}"), table_name="research_run_evidence"
        )
    op.drop_table("research_run_evidence")
    for column in [
        "decision_queue_item_id",
        "analysis_id",
        "ai_request_id",
        "prompt_version_id",
        "capability_id",
        "created_by",
        "project_id",
        "organization_id",
    ]:
        op.drop_index(op.f(f"ix_research_runs_{column}"), table_name="research_runs")
    op.drop_table("research_runs")
    for column in ["missing_evidence", "methodology_version", "citation_location"]:
        op.drop_column("research_evidence_citations", column)
