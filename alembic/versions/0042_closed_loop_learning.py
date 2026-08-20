"""Closed-loop revenue learning foundation."""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0042_closed_loop_learning"
down_revision: str | None = "0041_revenue_conversation"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def common() -> list[sa.Column]:
    return [
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
    ]


def upgrade() -> None:
    op.create_table(
        "learning_observations",
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("project_id", sa.Uuid()),
        sa.Column("product_id", sa.Uuid()),
        sa.Column("source_domain", sa.String(30), nullable=False),
        sa.Column("source_type", sa.String(50), nullable=False),
        sa.Column("source_record_id", sa.Uuid(), nullable=False),
        sa.Column("observation_type", sa.String(80), nullable=False),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("evidence_reference", sa.String(500), nullable=False),
        sa.Column("confidence", sa.Float()),
        sa.Column("metadata", sa.JSON(), nullable=False),
        *common(),
        sa.CheckConstraint(
            "confidence IS NULL OR confidence BETWEEN 0 AND 1", name="confidence_range"
        ),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"]),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "organization_id", "source_type", "source_record_id", "observation_type"
        ),
    )
    op.create_table(
        "root_cause_hypotheses",
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("project_id", sa.Uuid()),
        sa.Column("product_id", sa.Uuid()),
        sa.Column("hypothesis", sa.Text(), nullable=False),
        sa.Column("target_type", sa.String(50), nullable=False),
        sa.Column("target_id", sa.Uuid()),
        sa.Column("category", sa.String(60), nullable=False),
        sa.Column("evidence_coverage", sa.Float(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("methodology_version", sa.String(80), nullable=False),
        *common(),
        sa.CheckConstraint("confidence BETWEEN 0 AND 1", name="confidence_range"),
        sa.CheckConstraint("evidence_coverage BETWEEN 0 AND 1", name="coverage_range"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"]),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "root_cause_evidence_links",
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("hypothesis_id", sa.Uuid(), nullable=False),
        sa.Column("observation_id", sa.Uuid(), nullable=False),
        sa.Column("evidence_role", sa.String(20), nullable=False),
        *common(),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(
            ["hypothesis_id"], ["root_cause_hypotheses.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["observation_id"], ["learning_observations.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("hypothesis_id", "observation_id"),
    )
    op.create_table(
        "learning_conclusions",
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("hypothesis_id", sa.Uuid(), nullable=False),
        sa.Column("conclusion", sa.Text(), nullable=False),
        sa.Column("supporting_observation_ids", sa.JSON(), nullable=False),
        sa.Column("contradicting_observation_ids", sa.JSON(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("evidence_coverage", sa.Float(), nullable=False),
        sa.Column("methodology_version", sa.String(80), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("reviewer_id", sa.Uuid()),
        sa.Column("reviewed_at", sa.DateTime(timezone=True)),
        sa.Column("review_metadata", sa.JSON(), nullable=False),
        *common(),
        sa.CheckConstraint("confidence BETWEEN 0 AND 1", name="confidence_range"),
        sa.CheckConstraint("evidence_coverage BETWEEN 0 AND 1", name="coverage_range"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["hypothesis_id"], ["root_cause_hypotheses.id"]),
        sa.ForeignKeyConstraint(["reviewer_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "improvement_recommendations",
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("conclusion_id", sa.Uuid(), nullable=False),
        sa.Column("target_type", sa.String(40), nullable=False),
        sa.Column("target_id", sa.Uuid()),
        sa.Column("recommendation", sa.Text(), nullable=False),
        sa.Column("rationale", sa.Text(), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("decision_queue_item_id", sa.Uuid()),
        *common(),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["conclusion_id"], ["learning_conclusions.id"]),
        sa.ForeignKeyConstraint(["decision_queue_item_id"], ["decision_queue_items.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "recommendation_priority_assessments",
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("recommendation_id", sa.Uuid(), nullable=False),
        sa.Column("formula_version", sa.String(80), nullable=False),
        sa.Column("supplied_inputs", sa.JSON(), nullable=False),
        sa.Column("missing_inputs", sa.JSON(), nullable=False),
        sa.Column("calculated_score", sa.Float(), nullable=False),
        sa.Column("explanation_components", sa.JSON(), nullable=False),
        *common(),
        sa.CheckConstraint("calculated_score BETWEEN 0 AND 100", name="score_range"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(
            ["recommendation_id"], ["improvement_recommendations.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("recommendation_id"),
    )
    indexes = {
        "learning_observations": ["organization_id", "project_id", "product_id"],
        "root_cause_hypotheses": ["organization_id", "project_id", "product_id"],
        "root_cause_evidence_links": ["organization_id", "hypothesis_id", "observation_id"],
        "learning_conclusions": ["organization_id", "hypothesis_id"],
        "improvement_recommendations": ["organization_id", "conclusion_id"],
        "recommendation_priority_assessments": ["organization_id", "recommendation_id"],
    }
    for table, columns in indexes.items():
        for column in columns:
            op.create_index(op.f(f"ix_{table}_{column}"), table, [column])


def downgrade() -> None:
    for table in (
        "recommendation_priority_assessments",
        "improvement_recommendations",
        "learning_conclusions",
        "root_cause_evidence_links",
        "root_cause_hypotheses",
        "learning_observations",
    ):
        op.drop_table(table)
