"""Creative asset intelligence foundation."""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0027_creative_assets"
down_revision: str | None = "0026_ai_discovery_listing"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None
uuid = sa.Uuid()


def common() -> list[sa.Column]:
    return [
        sa.Column("id", uuid, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("organization_id", uuid, nullable=False),
    ]


def org_constraints() -> list[sa.Constraint]:
    return [
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.PrimaryKeyConstraint("id"),
    ]


def upgrade() -> None:
    op.add_column("creative_briefs", sa.Column("product_id", uuid, nullable=True))
    op.add_column("creative_briefs", sa.Column("objective", sa.Text(), nullable=True))
    op.add_column("creative_briefs", sa.Column("key_message", sa.Text(), nullable=True))
    op.add_column("creative_briefs", sa.Column("proof_requirements", sa.Text(), nullable=True))
    op.add_column("creative_briefs", sa.Column("cta_strategy", sa.Text(), nullable=True))
    op.add_column("creative_briefs", sa.Column("confidence", sa.Float(), nullable=True))
    op.execute(
        sa.text(
            """
            UPDATE creative_briefs
            SET product_id = (
                    SELECT product_id FROM creative_strategies
                    WHERE creative_strategies.id = creative_briefs.strategy_id
                ),
                objective = 'Legacy creative objective',
                key_message = hook,
                proof_requirements = proof_points,
                cta_strategy = cta,
                confidence = 0.5
            """
        )
    )
    with op.batch_alter_table("creative_briefs") as batch:
        batch.alter_column("product_id", existing_type=uuid, nullable=False)
        batch.alter_column("objective", existing_type=sa.Text(), nullable=False)
        batch.alter_column("key_message", existing_type=sa.Text(), nullable=False)
        batch.alter_column("proof_requirements", existing_type=sa.Text(), nullable=False)
        batch.alter_column("cta_strategy", existing_type=sa.Text(), nullable=False)
        batch.alter_column("confidence", existing_type=sa.Float(), nullable=False)
        batch.create_foreign_key(
            "fk_creative_briefs_product_id_products",
            "products",
            ["product_id"],
            ["id"],
            ondelete="CASCADE",
        )
        batch.create_check_constraint(
            op.f("ck_creative_briefs_confidence_range"),
            "confidence BETWEEN 0 AND 1",
        )
    op.create_index("ix_creative_briefs_product_id", "creative_briefs", ["product_id"])
    op.create_table(
        "creative_assets",
        *common(),
        sa.Column("product_id", uuid, nullable=False),
        sa.Column("asset_type", sa.String(20), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("source", sa.String(200), nullable=False),
        sa.Column("metadata", sa.JSON(), nullable=False),
        sa.Column("approval_status", sa.String(30), nullable=False),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="CASCADE"),
        *org_constraints(),
    )
    op.create_index("ix_creative_assets_organization_id", "creative_assets", ["organization_id"])
    op.create_index("ix_creative_assets_product_id", "creative_assets", ["product_id"])
    op.create_table(
        "creative_asset_versions",
        *common(),
        sa.Column("asset_id", uuid, nullable=False),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("variation_reason", sa.Text(), nullable=False),
        sa.Column("experiment_group", sa.String(100), nullable=False),
        sa.CheckConstraint("version_number > 0", name="version_number_positive"),
        sa.ForeignKeyConstraint(["asset_id"], ["creative_assets.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("asset_id", "version_number"),
        *org_constraints(),
    )
    op.create_index(
        "ix_creative_asset_versions_organization_id",
        "creative_asset_versions",
        ["organization_id"],
    )
    op.create_index("ix_creative_asset_versions_asset_id", "creative_asset_versions", ["asset_id"])
    op.create_table(
        "creative_performance_observations",
        *common(),
        sa.Column("asset_id", uuid, nullable=False),
        sa.Column("metric_type", sa.String(100), nullable=False),
        sa.Column("metric_value", sa.Numeric(19, 6), nullable=False),
        sa.Column("source", sa.String(200), nullable=False),
        sa.Column("period", sa.String(100), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.CheckConstraint("confidence BETWEEN 0 AND 1", name="confidence_range"),
        sa.ForeignKeyConstraint(["asset_id"], ["creative_assets.id"], ondelete="CASCADE"),
        *org_constraints(),
    )
    op.create_index(
        "ix_creative_performance_observations_organization_id",
        "creative_performance_observations",
        ["organization_id"],
    )
    op.create_index(
        "ix_creative_performance_observations_asset_id",
        "creative_performance_observations",
        ["asset_id"],
    )


def downgrade() -> None:
    op.drop_table("creative_performance_observations")
    op.drop_table("creative_asset_versions")
    op.drop_table("creative_assets")
    op.drop_index("ix_creative_briefs_product_id", table_name="creative_briefs")
    with op.batch_alter_table("creative_briefs") as batch:
        batch.drop_constraint(op.f("ck_creative_briefs_confidence_range"), type_="check")
        batch.drop_constraint("fk_creative_briefs_product_id_products", type_="foreignkey")
        for column in (
            "confidence",
            "cta_strategy",
            "proof_requirements",
            "key_message",
            "objective",
            "product_id",
        ):
            batch.drop_column(column)
