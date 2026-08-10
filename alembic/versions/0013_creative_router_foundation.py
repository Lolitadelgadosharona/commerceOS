"""Creative intelligence and multi-model router foundation.

Revision ID: 0013_creative_router
Revises: 0012_ai_sales_support
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0013_creative_router"
down_revision: str | None = "0012_ai_sales_support"
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
        "creative_asset_strategies",
        *common(),
        sa.Column("organization_id", uuid, nullable=False),
        sa.Column("product_id", uuid, nullable=False),
        sa.Column("creative_strategy_id", uuid, nullable=False),
        sa.Column("audience", sa.Text(), nullable=False),
        sa.Column("objective", sa.Text(), nullable=False),
        sa.Column("recommended_format", sa.String(30), nullable=False),
        sa.Column("creative_angle", sa.Text(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.CheckConstraint("confidence BETWEEN 0 AND 1", name="confidence_range"),
        org(),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"]),
        sa.ForeignKeyConstraint(["creative_strategy_id"], ["creative_strategies.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    indexes("creative_asset_strategies", "product_id")
    op.create_index(
        "ix_creative_asset_strategies_creative_strategy_id",
        "creative_asset_strategies",
        ["creative_strategy_id"],
    )
    op.create_table(
        "creative_model_providers",
        *common(),
        sa.Column("organization_id", uuid, nullable=False),
        sa.Column("provider_name", sa.String(150), nullable=False),
        sa.Column("capability_type", sa.String(30), nullable=False),
        sa.Column("quality_score", sa.Float(), nullable=False),
        sa.Column("cost_score", sa.Float(), nullable=False),
        sa.Column("speed_score", sa.Float(), nullable=False),
        sa.Column("availability", sa.Boolean(), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.CheckConstraint("quality_score BETWEEN 0 AND 100", name="quality_range"),
        sa.CheckConstraint("cost_score BETWEEN 0 AND 100", name="cost_range"),
        sa.CheckConstraint("speed_score BETWEEN 0 AND 100", name="speed_range"),
        org(),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("organization_id", "provider_name", "capability_type"),
    )
    op.create_index(
        "ix_creative_model_providers_organization_id",
        "creative_model_providers",
        ["organization_id"],
    )
    op.create_table(
        "creative_routing_decisions",
        *common(),
        sa.Column("organization_id", uuid, nullable=False),
        sa.Column("asset_strategy_id", uuid, nullable=False),
        sa.Column("capability_required", sa.String(30), nullable=False),
        sa.Column("selected_provider_id", uuid, nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("factor_snapshot", sa.JSON(), nullable=False),
        sa.Column("routing_score", sa.Float(), nullable=False),
        sa.Column("router_version", sa.String(40), nullable=False),
        sa.CheckConstraint("confidence BETWEEN 0 AND 1", name="confidence_range"),
        org(),
        sa.ForeignKeyConstraint(
            ["asset_strategy_id"], ["creative_asset_strategies.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["selected_provider_id"], ["creative_model_providers.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    indexes("creative_routing_decisions", "asset_strategy_id")
    op.create_index(
        "ix_creative_routing_decisions_selected_provider_id",
        "creative_routing_decisions",
        ["selected_provider_id"],
    )
    op.create_table(
        "creative_economic_assessments",
        *common(),
        sa.Column("organization_id", uuid, nullable=False),
        sa.Column("creative_strategy_id", uuid, nullable=False),
        sa.Column("estimated_production_cost", sa.Float(), nullable=False),
        sa.Column("expected_impact", sa.Float(), nullable=False),
        sa.Column("test_value", sa.Float(), nullable=False),
        sa.Column("profitability_score", sa.Float(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("formula_version", sa.String(40), nullable=False),
        sa.CheckConstraint("confidence BETWEEN 0 AND 1", name="confidence_range"),
        sa.CheckConstraint("profitability_score BETWEEN 0 AND 100", name="profitability_range"),
        org(),
        sa.ForeignKeyConstraint(["creative_strategy_id"], ["creative_strategies.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    indexes("creative_economic_assessments", "creative_strategy_id")
    op.create_table(
        "creative_pattern_references",
        *common(),
        sa.Column("organization_id", uuid, nullable=False),
        sa.Column("name", sa.String(250), nullable=False),
        sa.Column("pattern_type", sa.String(40), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("source_reference", sa.String(500), nullable=False),
        sa.Column("performance_notes", sa.Text(), nullable=False),
        org(),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("organization_id", "name", "pattern_type"),
    )
    op.create_index(
        "ix_creative_pattern_references_organization_id",
        "creative_pattern_references",
        ["organization_id"],
    )


def downgrade() -> None:
    for table in (
        "creative_pattern_references",
        "creative_economic_assessments",
        "creative_routing_decisions",
        "creative_model_providers",
        "creative_asset_strategies",
    ):
        op.drop_table(table)
