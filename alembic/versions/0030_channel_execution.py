"""Channel execution and creative distribution foundation."""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0030_channel_execution"
down_revision: str | None = "0029_creative_execution"
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


def indexes(table: str, columns: tuple[str, ...]) -> None:
    for column in columns:
        op.create_index(f"ix_{table}_{column}", table, [column])


def upgrade() -> None:
    op.create_table(
        "channel_execution_plans",
        *common(),
        sa.Column("project_id", uuid, nullable=False),
        sa.Column("channel", sa.String(50), nullable=False),
        sa.Column("creative_asset_id", uuid, nullable=False),
        sa.Column("objective", sa.Text(), nullable=False),
        sa.Column("target_audience", sa.Text(), nullable=False),
        sa.Column("execution_type", sa.String(30), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("created_by", uuid, nullable=False),
        sa.Column("approval_request_id", uuid, nullable=True),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"]),
        sa.ForeignKeyConstraint(["creative_asset_id"], ["creative_assets.id"]),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["approval_request_id"], ["approval_requests.id"]),
        *base_constraints(),
    )
    indexes(
        "channel_execution_plans",
        ("organization_id", "project_id", "creative_asset_id", "created_by"),
    )
    op.create_table(
        "creative_channel_experiments",
        *common(),
        sa.Column("channel_execution_plan_id", uuid, nullable=False),
        sa.Column("hypothesis", sa.Text(), nullable=False),
        sa.Column("creative_variant_ids", sa.JSON(), nullable=False),
        sa.Column("success_metrics", sa.JSON(), nullable=False),
        sa.Column("test_notes", sa.Text(), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.ForeignKeyConstraint(
            ["channel_execution_plan_id"], ["channel_execution_plans.id"], ondelete="CASCADE"
        ),
        *base_constraints(),
    )
    indexes("creative_channel_experiments", ("organization_id", "channel_execution_plan_id"))
    op.create_table(
        "distribution_records",
        *common(),
        sa.Column("creative_asset_id", uuid, nullable=False),
        sa.Column("channel", sa.String(50), nullable=False),
        sa.Column("distribution_status", sa.String(30), nullable=False),
        sa.Column("published_reference", sa.String(500), nullable=True),
        sa.Column("scheduled_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("actual_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("approval_request_id", uuid, nullable=True),
        sa.ForeignKeyConstraint(["creative_asset_id"], ["creative_assets.id"]),
        sa.ForeignKeyConstraint(["approval_request_id"], ["approval_requests.id"]),
        *base_constraints(),
    )
    indexes("distribution_records", ("organization_id", "creative_asset_id"))
    op.create_table(
        "channel_performance_observations",
        *common(),
        sa.Column("channel", sa.String(50), nullable=False),
        sa.Column("creative_asset_id", uuid, nullable=False),
        sa.Column("experiment_id", uuid, nullable=True),
        sa.Column("metric_name", sa.String(100), nullable=False),
        sa.Column("metric_value", sa.Numeric(19, 6), nullable=False),
        sa.Column("source", sa.String(200), nullable=False),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["creative_asset_id"], ["creative_assets.id"]),
        sa.ForeignKeyConstraint(
            ["experiment_id"], ["creative_channel_experiments.id"], ondelete="SET NULL"
        ),
        *base_constraints(),
    )
    indexes(
        "channel_performance_observations",
        ("organization_id", "creative_asset_id", "experiment_id"),
    )


def downgrade() -> None:
    op.drop_table("channel_performance_observations")
    op.drop_table("distribution_records")
    op.drop_table("creative_channel_experiments")
    op.drop_table("channel_execution_plans")
