"""Live revenue experiment support foundation.

Revision ID: 0066_live_revenue_support
Revises: 0065_revenue_operations
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0066_live_revenue_support"
down_revision: str | None = "0065_revenue_operations"
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
        "daily_revenue_runs",
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("revenue_experiment_id", sa.Uuid(), nullable=False),
        sa.Column("run_date", sa.Date(), nullable=False),
        sa.Column("industry", sa.String(120), nullable=False),
        sa.Column("target_geography", sa.String(240), nullable=False),
        sa.Column("generated_prospects", sa.Integer(), nullable=False),
        sa.Column("review_status", sa.String(30), nullable=False),
        sa.Column("created_by", sa.Uuid(), nullable=False),
        sa.Column("reviewed_by", sa.Uuid()),
        *common(),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["revenue_experiment_id"], ["revenue_experiments.id"]),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["reviewed_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "organization_id",
            "revenue_experiment_id",
            "run_date",
            "industry",
            "target_geography",
        ),
    )
    indexes(
        "daily_revenue_runs",
        ["organization_id", "revenue_experiment_id", "run_date", "created_by", "reviewed_by"],
    )

    op.create_table(
        "daily_revenue_run_prospects",
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("daily_revenue_run_id", sa.Uuid(), nullable=False),
        sa.Column("prospect_id", sa.Uuid(), nullable=False),
        sa.Column("priority_rank", sa.Integer(), nullable=False),
        sa.Column("priority_score", sa.Float()),
        sa.Column("evidence_reference", sa.String(500), nullable=False),
        *common(),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["daily_revenue_run_id"], ["daily_revenue_runs.id"]),
        sa.ForeignKeyConstraint(["prospect_id"], ["growth_prospects.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("daily_revenue_run_id", "prospect_id"),
    )
    indexes(
        "daily_revenue_run_prospects", ["organization_id", "daily_revenue_run_id", "prospect_id"]
    )

    op.create_table(
        "founder_action_items",
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("revenue_experiment_id", sa.Uuid()),
        sa.Column("prospect_id", sa.Uuid()),
        sa.Column("action_type", sa.String(40), nullable=False),
        sa.Column("source_type", sa.String(80), nullable=False),
        sa.Column("source_reference_id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(240), nullable=False),
        sa.Column("priority", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("assigned_to", sa.Uuid()),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.Column("decision_notes", sa.Text(), nullable=False),
        *common(),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["revenue_experiment_id"], ["revenue_experiments.id"]),
        sa.ForeignKeyConstraint(["prospect_id"], ["growth_prospects.id"]),
        sa.ForeignKeyConstraint(["assigned_to"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    indexes(
        "founder_action_items",
        ["organization_id", "revenue_experiment_id", "prospect_id", "assigned_to"],
    )

    op.create_table(
        "growth_external_data_connectors",
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(160), nullable=False),
        sa.Column("provider", sa.String(120), nullable=False),
        sa.Column("data_type", sa.String(40), nullable=False),
        sa.Column("collection_mode", sa.String(40), nullable=False),
        sa.Column("credential_reference", sa.String(500)),
        sa.Column("configuration", sa.JSON(), nullable=False),
        sa.Column("policy_reference", sa.String(500), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        *common(),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("organization_id", "name"),
    )
    indexes("growth_external_data_connectors", ["organization_id"])

    op.create_table(
        "customer_service_deliveries",
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("prospect_id", sa.Uuid(), nullable=False),
        sa.Column("offer_tracking_id", sa.Uuid(), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("owner_id", sa.Uuid(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True)),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.Column("customer_feedback_reference", sa.String(500)),
        *common(),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["prospect_id"], ["growth_prospects.id"]),
        sa.ForeignKeyConstraint(["offer_tracking_id"], ["revenue_offer_tracking.id"]),
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("organization_id", "offer_tracking_id"),
    )
    indexes(
        "customer_service_deliveries",
        ["organization_id", "prospect_id", "offer_tracking_id", "owner_id"],
    )

    op.create_table(
        "customer_delivery_items",
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("delivery_id", sa.Uuid(), nullable=False),
        sa.Column("item_type", sa.String(30), nullable=False),
        sa.Column("title", sa.String(240), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("due_at", sa.DateTime(timezone=True)),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.Column("evidence_reference", sa.String(500)),
        *common(),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["delivery_id"], ["customer_service_deliveries.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("delivery_id", "sequence"),
    )
    indexes("customer_delivery_items", ["organization_id", "delivery_id"])


def downgrade() -> None:
    for table, columns in [
        ("customer_delivery_items", ["delivery_id", "organization_id"]),
        (
            "customer_service_deliveries",
            ["owner_id", "offer_tracking_id", "prospect_id", "organization_id"],
        ),
        ("growth_external_data_connectors", ["organization_id"]),
        (
            "founder_action_items",
            ["assigned_to", "prospect_id", "revenue_experiment_id", "organization_id"],
        ),
        ("daily_revenue_run_prospects", ["prospect_id", "daily_revenue_run_id", "organization_id"]),
        (
            "daily_revenue_runs",
            ["reviewed_by", "created_by", "run_date", "revenue_experiment_id", "organization_id"],
        ),
    ]:
        for column in columns:
            op.drop_index(op.f(f"ix_{table}_{column}"), table_name=table)
        op.drop_table(table)
