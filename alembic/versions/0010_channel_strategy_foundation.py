"""Channel strategy and conversion path foundation.

Revision ID: 0010_channel_strategy
Revises: 0009_creative_strategy
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0010_channel_strategy"
down_revision: str | None = "0009_creative_strategy"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None
uuid = sa.Uuid()


def common() -> list[sa.Column]:
    return [
        sa.Column("id", uuid, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
    ]


def indexes(table: str, reference: str) -> None:
    op.create_index(f"ix_{table}_organization_id", table, ["organization_id"])
    op.create_index(f"ix_{table}_{reference}", table, [reference])


def org() -> sa.ForeignKeyConstraint:
    return sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"])


def upgrade() -> None:
    op.create_table(
        "channel_strategies",
        *common(),
        sa.Column("organization_id", uuid, nullable=False),
        sa.Column("project_id", uuid),
        sa.Column("product_id", uuid, nullable=False),
        sa.Column("creative_strategy_id", uuid),
        sa.Column("market", sa.String(150), nullable=False),
        sa.Column("geography", sa.String(150), nullable=False),
        sa.Column("audience", sa.Text(), nullable=False),
        sa.Column("business_model", sa.String(10), nullable=False),
        sa.Column("objective", sa.Text(), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        org(),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"]),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["creative_strategy_id"], ["creative_strategies.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    indexes("channel_strategies", "product_id")
    op.create_table(
        "channel_candidates",
        *common(),
        sa.Column("organization_id", uuid, nullable=False),
        sa.Column("strategy_id", uuid, nullable=False),
        sa.Column("channel", sa.String(80), nullable=False),
        sa.Column("distribution_mode", sa.String(30), nullable=False),
        sa.Column("suitability_score", sa.Float(), nullable=False),
        sa.Column("confidence_score", sa.Float(), nullable=False),
        sa.Column("recommendation", sa.String(30), nullable=False),
        sa.Column("reason", sa.Text()),
        sa.Column("exclusion_reason", sa.Text()),
        sa.CheckConstraint("suitability_score BETWEEN 0 AND 100", name="suitability_range"),
        sa.CheckConstraint("confidence_score BETWEEN 0 AND 1", name="confidence_range"),
        org(),
        sa.ForeignKeyConstraint(["strategy_id"], ["channel_strategies.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("strategy_id", "channel"),
    )
    indexes("channel_candidates", "strategy_id")
    factor_columns = [
        sa.Column(name, sa.Float())
        for name in (
            "target_customer_fit",
            "product_fit",
            "buying_intent",
            "visual_fit",
            "organic_potential",
            "search_discovery_potential",
            "content_cost",
            "competition",
            "expected_acquisition_cost",
            "historical_performance_confidence",
            "conversion_path_fit",
        )
    ]
    op.create_table(
        "channel_opportunity_scores",
        *common(),
        sa.Column("organization_id", uuid, nullable=False),
        sa.Column("candidate_id", uuid, nullable=False),
        *factor_columns,
        sa.Column("overall_score", sa.Float(), nullable=False),
        sa.Column("evidence_coverage", sa.Float(), nullable=False),
        sa.Column("formula_version", sa.String(30), nullable=False),
        sa.CheckConstraint("overall_score BETWEEN 0 AND 100", name="overall_range"),
        sa.CheckConstraint("evidence_coverage BETWEEN 0 AND 1", name="coverage_range"),
        org(),
        sa.ForeignKeyConstraint(["candidate_id"], ["channel_candidates.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("candidate_id"),
    )
    indexes("channel_opportunity_scores", "candidate_id")
    op.create_table(
        "conversion_paths",
        *common(),
        sa.Column("organization_id", uuid, nullable=False),
        sa.Column("strategy_id", uuid, nullable=False),
        sa.Column("name", sa.String(250), nullable=False),
        sa.Column("business_model", sa.String(10), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        org(),
        sa.ForeignKeyConstraint(["strategy_id"], ["channel_strategies.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    indexes("conversion_paths", "strategy_id")
    op.create_table(
        "conversion_path_steps",
        *common(),
        sa.Column("organization_id", uuid, nullable=False),
        sa.Column("path_id", uuid, nullable=False),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column("step_type", sa.String(50), nullable=False),
        sa.Column("channel", sa.String(80)),
        sa.Column("responsible_domain", sa.String(30), nullable=False),
        sa.Column("human_required", sa.Boolean(), nullable=False),
        sa.Column("approval_required", sa.Boolean(), nullable=False),
        org(),
        sa.ForeignKeyConstraint(["path_id"], ["conversion_paths.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("path_id", "sequence"),
    )
    indexes("conversion_path_steps", "path_id")
    op.create_table(
        "channel_measurement_plans",
        *common(),
        sa.Column("organization_id", uuid, nullable=False),
        sa.Column("strategy_id", uuid, nullable=False),
        sa.Column("metrics", sa.JSON(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=False),
        org(),
        sa.ForeignKeyConstraint(["strategy_id"], ["channel_strategies.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("strategy_id"),
    )
    indexes("channel_measurement_plans", "strategy_id")
    op.create_table(
        "channel_decision_evidence",
        *common(),
        sa.Column("organization_id", uuid, nullable=False),
        sa.Column("strategy_id", uuid, nullable=False),
        sa.Column("evidence_type", sa.String(80), nullable=False),
        sa.Column("source_reference", sa.String(500), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("confidence_score", sa.Float(), nullable=False),
        sa.CheckConstraint("confidence_score BETWEEN 0 AND 1", name="confidence_range"),
        org(),
        sa.ForeignKeyConstraint(["strategy_id"], ["channel_strategies.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("strategy_id", "evidence_type", "source_reference"),
    )
    indexes("channel_decision_evidence", "strategy_id")


def downgrade() -> None:
    for table in (
        "channel_decision_evidence",
        "channel_measurement_plans",
        "conversion_path_steps",
        "conversion_paths",
        "channel_opportunity_scores",
        "channel_candidates",
        "channel_strategies",
    ):
        op.drop_table(table)
