"""Growth experiment and performance foundation."""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0040_growth_experiments"
down_revision: str | None = "0039_creative_production"
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
        "growth_creative_experiments",
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("creative_strategy_id", sa.Uuid(), nullable=False),
        sa.Column("hypothesis", sa.Text(), nullable=False),
        sa.Column("objective", sa.Text(), nullable=False),
        sa.Column("audience", sa.Text(), nullable=False),
        sa.Column("channel", sa.String(30), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("owner_id", sa.Uuid(), nullable=False),
        sa.Column("approval_request_id", sa.Uuid(), nullable=True),
        *common(),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"]),
        sa.ForeignKeyConstraint(["creative_strategy_id"], ["creative_strategies.id"]),
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["approval_request_id"], ["approval_requests.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "growth_experiment_variants",
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("experiment_id", sa.Uuid(), nullable=False),
        sa.Column("creative_asset_id", sa.Uuid(), nullable=False),
        sa.Column("variant_name", sa.String(150), nullable=False),
        sa.Column("hypothesis", sa.Text(), nullable=False),
        sa.Column("expected_outcome", sa.Text(), nullable=False),
        *common(),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(
            ["experiment_id"], ["growth_creative_experiments.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["creative_asset_id"], ["creative_assets.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("experiment_id", "variant_name"),
    )
    op.create_table(
        "distribution_campaigns",
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("experiment_id", sa.Uuid(), nullable=False),
        sa.Column("creative_asset_id", sa.Uuid(), nullable=False),
        sa.Column("channel", sa.String(30), nullable=False),
        sa.Column("approval_state", sa.String(20), nullable=False),
        sa.Column("lifecycle_state", sa.String(20), nullable=False),
        sa.Column("approval_request_id", sa.Uuid(), nullable=True),
        *common(),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(
            ["experiment_id"], ["growth_creative_experiments.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["creative_asset_id"], ["creative_assets.id"]),
        sa.ForeignKeyConstraint(["approval_request_id"], ["approval_requests.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "growth_performance_observations",
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("creative_asset_id", sa.Uuid(), nullable=False),
        sa.Column("experiment_id", sa.Uuid(), nullable=False),
        sa.Column("impressions", sa.Integer(), nullable=False),
        sa.Column("clicks", sa.Integer(), nullable=False),
        sa.Column("engagement", sa.Numeric(19, 6), nullable=False),
        sa.Column("conversion", sa.Numeric(19, 6), nullable=False),
        sa.Column("revenue_observation_id", sa.Uuid(), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=False),
        *common(),
        sa.CheckConstraint("impressions >= 0", name="impressions_nonnegative"),
        sa.CheckConstraint("clicks >= 0", name="clicks_nonnegative"),
        sa.CheckConstraint("engagement >= 0", name="engagement_nonnegative"),
        sa.CheckConstraint("conversion >= 0", name="conversion_nonnegative"),
        sa.CheckConstraint("confidence BETWEEN 0 AND 1", name="confidence_range"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["creative_asset_id"], ["creative_assets.id"]),
        sa.ForeignKeyConstraint(
            ["experiment_id"], ["growth_creative_experiments.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["revenue_observation_id"], ["revenue_observations.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "growth_learning_signals",
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("source_experiment_id", sa.Uuid(), nullable=False),
        sa.Column("pattern_reference_id", sa.Uuid(), nullable=True),
        sa.Column("pattern", sa.Text(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("recommendation", sa.Text(), nullable=False),
        *common(),
        sa.CheckConstraint("confidence BETWEEN 0 AND 1", name="confidence_range"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(
            ["source_experiment_id"], ["growth_creative_experiments.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["pattern_reference_id"], ["creative_pattern_references.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "growth_learning_observation_links",
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("learning_signal_id", sa.Uuid(), nullable=False),
        sa.Column("observation_id", sa.Uuid(), nullable=False),
        *common(),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(
            ["learning_signal_id"], ["growth_learning_signals.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["observation_id"], ["growth_performance_observations.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("learning_signal_id", "observation_id"),
    )
    for table, columns in {
        "growth_creative_experiments": [
            "organization_id",
            "project_id",
            "creative_strategy_id",
            "owner_id",
            "approval_request_id",
        ],
        "growth_experiment_variants": ["organization_id", "experiment_id", "creative_asset_id"],
        "distribution_campaigns": [
            "organization_id",
            "experiment_id",
            "creative_asset_id",
            "approval_request_id",
        ],
        "growth_performance_observations": [
            "organization_id",
            "creative_asset_id",
            "experiment_id",
            "revenue_observation_id",
        ],
        "growth_learning_signals": [
            "organization_id",
            "source_experiment_id",
            "pattern_reference_id",
        ],
        "growth_learning_observation_links": [
            "organization_id",
            "learning_signal_id",
            "observation_id",
        ],
    }.items():
        for column in columns:
            op.create_index(op.f(f"ix_{table}_{column}"), table, [column])


def downgrade() -> None:
    for table in (
        "growth_learning_observation_links",
        "growth_learning_signals",
        "growth_performance_observations",
        "distribution_campaigns",
        "growth_experiment_variants",
        "growth_creative_experiments",
    ):
        op.drop_table(table)
