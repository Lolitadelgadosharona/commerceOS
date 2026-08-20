"""Governed AI opportunity discovery foundation.

Revision ID: 0045_ai_opportunity_discovery
Revises: 0044_ai_research_ops
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0045_ai_opportunity_discovery"
down_revision: str | None = "0044_ai_research_ops"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "opportunity_discovery_runs",
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("project_id", sa.Uuid()),
        sa.Column("discovery_type", sa.String(60), nullable=False),
        sa.Column("objective", sa.Text(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("methodology_version", sa.String(80), nullable=False),
        sa.Column("research_run_id", sa.Uuid()),
        sa.Column("capability_id", sa.Uuid(), nullable=False),
        sa.Column("prompt_version_id", sa.Uuid()),
        sa.Column("ai_request_id", sa.Uuid()),
        sa.Column("created_by", sa.Uuid(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True)),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.Column("failure_reason", sa.Text()),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"]),
        sa.ForeignKeyConstraint(["research_run_id"], ["research_runs.id"]),
        sa.ForeignKeyConstraint(["capability_id"], ["ai_model_capabilities.id"]),
        sa.ForeignKeyConstraint(["prompt_version_id"], ["prompt_versions.id"]),
        sa.ForeignKeyConstraint(["ai_request_id"], ["ai_requests.id"]),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    for column in [
        "organization_id",
        "project_id",
        "research_run_id",
        "capability_id",
        "prompt_version_id",
        "ai_request_id",
        "created_by",
    ]:
        op.create_index(
            op.f(f"ix_opportunity_discovery_runs_{column}"), "opportunity_discovery_runs", [column]
        )
    op.create_table(
        "opportunity_discovery_evidence",
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("discovery_run_id", sa.Uuid(), nullable=False),
        sa.Column("evidence_type", sa.String(50), nullable=False),
        sa.Column("evidence_id", sa.Uuid(), nullable=False),
        sa.Column("source_reference", sa.String(500), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.CheckConstraint("confidence BETWEEN 0 AND 1", name="disc_evidence_conf"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(
            ["discovery_run_id"], ["opportunity_discovery_runs.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("discovery_run_id", "evidence_type", "evidence_id"),
    )
    for column in ["organization_id", "discovery_run_id", "evidence_id"]:
        op.create_index(
            op.f(f"ix_opportunity_discovery_evidence_{column}"),
            "opportunity_discovery_evidence",
            [column],
        )
    op.create_table(
        "opportunity_discovery_candidates",
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("discovery_run_id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(250), nullable=False),
        sa.Column("problem_statement", sa.Text(), nullable=False),
        sa.Column("customer_segment", sa.Text(), nullable=False),
        sa.Column("evidence_summary", sa.Text(), nullable=False),
        sa.Column("evidence_references", sa.JSON(), nullable=False),
        sa.Column("solution_direction", sa.Text(), nullable=False),
        sa.Column("customer_language", sa.JSON(), nullable=False),
        sa.Column("confidence_score", sa.Float(), nullable=False),
        sa.Column("risk_summary", sa.JSON(), nullable=False),
        sa.Column("open_questions", sa.JSON(), nullable=False),
        sa.Column("missing_evidence", sa.JSON(), nullable=False),
        sa.Column("advisory_score", sa.Float(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("methodology_version", sa.String(80), nullable=False),
        sa.Column("decision_queue_item_id", sa.Uuid()),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.CheckConstraint("confidence_score BETWEEN 0 AND 1", name="disc_candidate_conf"),
        sa.CheckConstraint("advisory_score BETWEEN 0 AND 100", name="disc_candidate_score"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(
            ["discovery_run_id"], ["opportunity_discovery_runs.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["decision_queue_item_id"], ["decision_queue_items.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("discovery_run_id"),
    )
    for column in ["organization_id", "decision_queue_item_id"]:
        op.create_index(
            op.f(f"ix_opportunity_discovery_candidates_{column}"),
            "opportunity_discovery_candidates",
            [column],
        )


def downgrade() -> None:
    for column in ["decision_queue_item_id", "organization_id"]:
        op.drop_index(
            op.f(f"ix_opportunity_discovery_candidates_{column}"),
            table_name="opportunity_discovery_candidates",
        )
    op.drop_table("opportunity_discovery_candidates")
    for column in ["evidence_id", "discovery_run_id", "organization_id"]:
        op.drop_index(
            op.f(f"ix_opportunity_discovery_evidence_{column}"),
            table_name="opportunity_discovery_evidence",
        )
    op.drop_table("opportunity_discovery_evidence")
    for column in [
        "created_by",
        "ai_request_id",
        "prompt_version_id",
        "capability_id",
        "research_run_id",
        "project_id",
        "organization_id",
    ]:
        op.drop_index(
            op.f(f"ix_opportunity_discovery_runs_{column}"), table_name="opportunity_discovery_runs"
        )
    op.drop_table("opportunity_discovery_runs")
