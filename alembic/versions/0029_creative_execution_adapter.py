"""Creative execution adapter foundation."""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0029_creative_execution"
down_revision: str | None = "0028_creative_generation"
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
    op.add_column(
        "creative_generation_jobs",
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "creative_generation_jobs",
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column("creative_generation_jobs", sa.Column("failure_reason", sa.Text(), nullable=True))
    op.add_column(
        "creative_generation_jobs",
        sa.Column("retry_count", sa.Integer(), server_default="0", nullable=False),
    )
    op.create_table(
        "creative_execution_records",
        *common(),
        sa.Column("generation_job_id", uuid, nullable=False),
        sa.Column("provider_id", uuid, nullable=False),
        sa.Column("execution_status", sa.String(30), nullable=False),
        sa.Column("input_snapshot", sa.JSON(), nullable=False),
        sa.Column("output_reference", sa.String(500), nullable=True),
        sa.Column("estimated_cost", sa.Numeric(19, 6), nullable=False),
        sa.Column("actual_cost", sa.Numeric(19, 6), nullable=True),
        sa.Column("duration", sa.Float(), nullable=False),
        sa.CheckConstraint("estimated_cost >= 0", name="estimated_cost_nonnegative"),
        sa.CheckConstraint(
            "actual_cost IS NULL OR actual_cost >= 0", name="actual_cost_nonnegative"
        ),
        sa.CheckConstraint("duration >= 0", name="duration_nonnegative"),
        sa.ForeignKeyConstraint(
            ["generation_job_id"], ["creative_generation_jobs.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["provider_id"], ["creative_provider_capabilities.id"]),
        *base_constraints(),
    )
    for column in ("organization_id", "generation_job_id", "provider_id"):
        op.create_index(
            f"ix_creative_execution_records_{column}", "creative_execution_records", [column]
        )
    op.create_table(
        "creative_artifacts",
        *common(),
        sa.Column("generation_job_id", uuid, nullable=False),
        sa.Column("asset_id", uuid, nullable=False),
        sa.Column("artifact_type", sa.String(30), nullable=False),
        sa.Column("artifact_reference", sa.String(500), nullable=False),
        sa.Column("validation_status", sa.String(30), nullable=False),
        sa.Column("metadata", sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(
            ["generation_job_id"], ["creative_generation_jobs.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["asset_id"], ["creative_assets.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("generation_job_id", "asset_id"),
        *base_constraints(),
    )
    for column in ("organization_id", "generation_job_id", "asset_id"):
        op.create_index(f"ix_creative_artifacts_{column}", "creative_artifacts", [column])
    op.create_table(
        "creative_generation_cost_observations",
        *common(),
        sa.Column("provider_id", uuid, nullable=False),
        sa.Column("job_id", uuid, nullable=False),
        sa.Column("estimated_cost", sa.Numeric(19, 6), nullable=False),
        sa.Column("actual_cost", sa.Numeric(19, 6), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("estimated_cost >= 0", name="est_nonneg"),
        sa.CheckConstraint("actual_cost >= 0", name="act_nonneg"),
        sa.ForeignKeyConstraint(["provider_id"], ["creative_provider_capabilities.id"]),
        sa.ForeignKeyConstraint(["job_id"], ["creative_generation_jobs.id"], ondelete="CASCADE"),
        *base_constraints(),
    )
    for column in ("organization_id", "provider_id", "job_id"):
        op.create_index(
            f"ix_creative_generation_cost_observations_{column}",
            "creative_generation_cost_observations",
            [column],
        )


def downgrade() -> None:
    op.drop_table("creative_generation_cost_observations")
    op.drop_table("creative_artifacts")
    op.drop_table("creative_execution_records")
    op.drop_column("creative_generation_jobs", "retry_count")
    op.drop_column("creative_generation_jobs", "failure_reason")
    op.drop_column("creative_generation_jobs", "completed_at")
    op.drop_column("creative_generation_jobs", "started_at")
