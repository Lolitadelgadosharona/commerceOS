"""Revenue validation experiment foundation.

Revision ID: 0060_revenue_validation
Revises: 0059_revenue_execution
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0060_revenue_validation"
down_revision: str | None = "0059_revenue_execution"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def common() -> list[sa.Column]:
    return [
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
    ]


def indexes(table: str, columns: list[str]) -> None:
    for column in columns:
        op.create_index(op.f(f"ix_{table}_{column}"), table, [column])


def upgrade() -> None:
    with op.batch_alter_table("revenue_experiments") as batch:
        batch.add_column(sa.Column("industry_profile_id", sa.Uuid()))
        batch.add_column(sa.Column("segment", sa.String(200), nullable=False, server_default=""))
        batch.add_column(
            sa.Column("target_count", sa.Integer(), nullable=False, server_default="0")
        )
        batch.add_column(sa.Column("start_date", sa.Date()))
        batch.add_column(
            sa.Column("success_metrics", sa.JSON(), nullable=False, server_default="{}")
        )
        batch.create_foreign_key(
            op.f("fk_revenue_experiments_industry_profile_id_industry_growth_profiles"),
            "industry_growth_profiles",
            ["industry_profile_id"],
            ["id"],
        )
        batch.create_index(
            op.f("ix_revenue_experiments_industry_profile_id"), ["industry_profile_id"]
        )
    with op.batch_alter_table("revenue_experiments") as batch:
        batch.alter_column("segment", server_default=None)
        batch.alter_column("target_count", server_default=None)
        batch.alter_column("success_metrics", server_default=None)

    op.create_table(
        "offer_experiments",
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("revenue_experiment_id", sa.Uuid(), nullable=False),
        sa.Column("offer_type", sa.String(120), nullable=False),
        sa.Column("prospect_segment", sa.String(200), nullable=False),
        sa.Column("hypothesis", sa.Text(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        *common(),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(
            ["revenue_experiment_id"], ["revenue_experiments.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("revenue_experiment_id", "offer_type", "prospect_segment"),
    )
    indexes("offer_experiments", ["organization_id", "revenue_experiment_id"])

    op.create_table(
        "offer_experiment_outcomes",
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("offer_experiment_id", sa.Uuid(), nullable=False),
        sa.Column("prospect_id", sa.Uuid(), nullable=False),
        sa.Column("outreach_sent", sa.Boolean(), nullable=False),
        sa.Column("replied", sa.Boolean(), nullable=False),
        sa.Column("positive_reply", sa.Boolean(), nullable=False),
        sa.Column("converted", sa.Boolean(), nullable=False),
        sa.Column("revenue_observation_id", sa.Uuid()),
        *common(),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(
            ["offer_experiment_id"], ["offer_experiments.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["prospect_id"], ["growth_prospects.id"]),
        sa.ForeignKeyConstraint(["revenue_observation_id"], ["revenue_observations.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("offer_experiment_id", "prospect_id"),
    )
    indexes(
        "offer_experiment_outcomes",
        ["organization_id", "offer_experiment_id", "prospect_id", "revenue_observation_id"],
    )

    op.create_table(
        "experiment_feedback_signals",
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("revenue_experiment_id", sa.Uuid(), nullable=False),
        sa.Column("offer_experiment_id", sa.Uuid()),
        sa.Column("source_type", sa.String(40), nullable=False),
        sa.Column("source_reference", sa.String(500), nullable=False),
        sa.Column("objection_category", sa.String(80)),
        sa.Column("frequency", sa.Integer(), nullable=False),
        sa.Column("industry", sa.String(120), nullable=False),
        sa.Column("recommended_response", sa.Text(), nullable=False),
        sa.Column("learning_signal", sa.Text(), nullable=False),
        sa.Column("industry_learning_signal_id", sa.Uuid()),
        *common(),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(
            ["revenue_experiment_id"], ["revenue_experiments.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["offer_experiment_id"], ["offer_experiments.id"]),
        sa.ForeignKeyConstraint(["industry_learning_signal_id"], ["industry_learning_signals.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    indexes(
        "experiment_feedback_signals",
        [
            "organization_id",
            "revenue_experiment_id",
            "offer_experiment_id",
            "industry_learning_signal_id",
        ],
    )


def downgrade() -> None:
    for table, columns in [
        (
            "experiment_feedback_signals",
            [
                "industry_learning_signal_id",
                "offer_experiment_id",
                "revenue_experiment_id",
                "organization_id",
            ],
        ),
        (
            "offer_experiment_outcomes",
            ["revenue_observation_id", "prospect_id", "offer_experiment_id", "organization_id"],
        ),
        ("offer_experiments", ["revenue_experiment_id", "organization_id"]),
    ]:
        for column in columns:
            op.drop_index(op.f(f"ix_{table}_{column}"), table_name=table)
        op.drop_table(table)
    with op.batch_alter_table("revenue_experiments") as batch:
        batch.drop_index(op.f("ix_revenue_experiments_industry_profile_id"))
        batch.drop_constraint(
            op.f("fk_revenue_experiments_industry_profile_id_industry_growth_profiles"),
            type_="foreignkey",
        )
        batch.drop_column("success_metrics")
        batch.drop_column("start_date")
        batch.drop_column("target_count")
        batch.drop_column("segment")
        batch.drop_column("industry_profile_id")
