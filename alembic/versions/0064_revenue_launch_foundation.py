"""Revenue launch foundation.

Revision ID: 0064_revenue_launch_foundation
Revises: 0063_revenue_machine_completion
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0064_revenue_launch_foundation"
down_revision: str | None = "0063_revenue_machine_completion"
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
    op.create_table(
        "prospect_revenue_pipelines",
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("prospect_id", sa.Uuid(), nullable=False),
        sa.Column("stage", sa.String(30), nullable=False),
        sa.Column("owner_id", sa.Uuid(), nullable=False),
        sa.Column("stage_entered_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("notes", sa.Text(), nullable=False),
        *common(),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["prospect_id"], ["growth_prospects.id"]),
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("organization_id", "prospect_id"),
    )
    indexes("prospect_revenue_pipelines", ["organization_id", "prospect_id", "owner_id"])
    op.create_table(
        "revenue_offer_tracking",
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("prospect_id", sa.Uuid(), nullable=False),
        sa.Column("recommendation_id", sa.Uuid()),
        sa.Column("offer_name", sa.String(200), nullable=False),
        sa.Column("price", sa.Numeric(18, 2)),
        sa.Column("currency", sa.String(3)),
        sa.Column("scope", sa.Text(), nullable=False),
        sa.Column("customer_response", sa.Text()),
        sa.Column("status", sa.String(20), nullable=False),
        *common(),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["prospect_id"], ["growth_prospects.id"]),
        sa.ForeignKeyConstraint(["recommendation_id"], ["growth_offer_recommendations.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    indexes("revenue_offer_tracking", ["organization_id", "prospect_id", "recommendation_id"])
    op.create_table(
        "payment_readiness_records",
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("prospect_id", sa.Uuid(), nullable=False),
        sa.Column("offer_tracking_id", sa.Uuid(), nullable=False),
        sa.Column("payment_provider_reference", sa.String(500)),
        sa.Column("payment_link", sa.String(1000)),
        sa.Column("invoice_reference", sa.String(500)),
        sa.Column("payment_status", sa.String(30), nullable=False),
        sa.Column("revenue_observation_id", sa.Uuid()),
        *common(),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["prospect_id"], ["growth_prospects.id"]),
        sa.ForeignKeyConstraint(["offer_tracking_id"], ["revenue_offer_tracking.id"]),
        sa.ForeignKeyConstraint(["revenue_observation_id"], ["revenue_observations.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    indexes(
        "payment_readiness_records",
        ["organization_id", "prospect_id", "offer_tracking_id", "revenue_observation_id"],
    )
    op.create_table(
        "customer_lifecycle_events",
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("prospect_id", sa.Uuid(), nullable=False),
        sa.Column("lifecycle_type", sa.String(40), nullable=False),
        sa.Column("source_reference", sa.String(500), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("notes", sa.Text(), nullable=False),
        sa.Column("metadata", sa.JSON(), nullable=False),
        sa.Column("recorded_by", sa.Uuid(), nullable=False),
        *common(),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["prospect_id"], ["growth_prospects.id"]),
        sa.ForeignKeyConstraint(["recorded_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    indexes("customer_lifecycle_events", ["organization_id", "prospect_id", "recorded_by"])


def downgrade() -> None:
    for table, columns in [
        ("customer_lifecycle_events", ["recorded_by", "prospect_id", "organization_id"]),
        (
            "payment_readiness_records",
            ["revenue_observation_id", "offer_tracking_id", "prospect_id", "organization_id"],
        ),
        ("revenue_offer_tracking", ["recommendation_id", "prospect_id", "organization_id"]),
        ("prospect_revenue_pipelines", ["owner_id", "prospect_id", "organization_id"]),
    ]:
        for column in columns:
            op.drop_index(op.f(f"ix_{table}_{column}"), table_name=table)
        op.drop_table(table)
