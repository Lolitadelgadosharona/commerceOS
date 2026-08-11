"""Creative generation workflow foundation."""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0028_creative_generation"
down_revision: str | None = "0027_creative_assets"
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


def base_constraints() -> list[sa.Constraint]:
    return [
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.PrimaryKeyConstraint("id"),
    ]


def upgrade() -> None:
    op.create_table(
        "creative_generation_requests",
        *common(),
        sa.Column("creative_brief_id", uuid, nullable=False),
        sa.Column("asset_type", sa.String(20), nullable=False),
        sa.Column("platform", sa.String(50), nullable=False),
        sa.Column("objective", sa.Text(), nullable=False),
        sa.Column("generation_parameters", sa.JSON(), nullable=False),
        sa.Column("requested_by", uuid, nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.ForeignKeyConstraint(["creative_brief_id"], ["creative_briefs.id"]),
        sa.ForeignKeyConstraint(["requested_by"], ["users.id"]),
        *base_constraints(),
    )
    op.create_index(
        "ix_creative_generation_requests_organization_id",
        "creative_generation_requests",
        ["organization_id"],
    )
    op.create_index(
        "ix_creative_generation_requests_creative_brief_id",
        "creative_generation_requests",
        ["creative_brief_id"],
    )
    op.create_index(
        "ix_creative_generation_requests_requested_by",
        "creative_generation_requests",
        ["requested_by"],
    )
    op.create_table(
        "creative_provider_capabilities",
        *common(),
        sa.Column("provider_name", sa.String(150), nullable=False),
        sa.Column("provider_type", sa.String(30), nullable=False),
        sa.Column("capabilities", sa.JSON(), nullable=False),
        sa.Column("cost_model", sa.JSON(), nullable=False),
        sa.Column("availability", sa.Boolean(), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.UniqueConstraint("organization_id", "provider_name", "provider_type"),
        *base_constraints(),
    )
    op.create_index(
        "ix_creative_provider_capabilities_organization_id",
        "creative_provider_capabilities",
        ["organization_id"],
    )
    op.create_table(
        "creative_generation_jobs",
        *common(),
        sa.Column("request_id", uuid, nullable=False),
        sa.Column("provider_id", uuid, nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("input_reference", sa.String(500), nullable=False),
        sa.Column("output_reference", sa.String(500), nullable=True),
        sa.Column("estimated_cost", sa.Numeric(19, 6), nullable=False),
        sa.Column("actual_cost", sa.Numeric(19, 6), nullable=True),
        sa.Column("latency", sa.Float(), nullable=True),
        sa.CheckConstraint("estimated_cost >= 0", name="estimated_cost_nonnegative"),
        sa.CheckConstraint(
            "actual_cost IS NULL OR actual_cost >= 0", name="actual_cost_nonnegative"
        ),
        sa.CheckConstraint("latency IS NULL OR latency >= 0", name="latency_nonnegative"),
        sa.ForeignKeyConstraint(
            ["request_id"], ["creative_generation_requests.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["provider_id"], ["creative_provider_capabilities.id"]),
        *base_constraints(),
    )
    op.create_index(
        "ix_creative_generation_jobs_organization_id",
        "creative_generation_jobs",
        ["organization_id"],
    )
    op.create_index(
        "ix_creative_generation_jobs_request_id", "creative_generation_jobs", ["request_id"]
    )
    op.create_index(
        "ix_creative_generation_jobs_provider_id", "creative_generation_jobs", ["provider_id"]
    )
    op.create_table(
        "creative_quality_reviews",
        *common(),
        sa.Column("asset_id", uuid, nullable=False),
        sa.Column("review_type", sa.String(50), nullable=False),
        sa.Column("score", sa.Float(), nullable=False),
        sa.Column("issues", sa.JSON(), nullable=False),
        sa.Column("recommendation", sa.Text(), nullable=False),
        sa.CheckConstraint("score BETWEEN 0 AND 100", name="score_range"),
        sa.ForeignKeyConstraint(["asset_id"], ["creative_assets.id"], ondelete="CASCADE"),
        *base_constraints(),
    )
    op.create_index(
        "ix_creative_quality_reviews_organization_id",
        "creative_quality_reviews",
        ["organization_id"],
    )
    op.create_index(
        "ix_creative_quality_reviews_asset_id", "creative_quality_reviews", ["asset_id"]
    )


def downgrade() -> None:
    op.drop_table("creative_quality_reviews")
    op.drop_table("creative_generation_jobs")
    op.drop_table("creative_provider_capabilities")
    op.drop_table("creative_generation_requests")
