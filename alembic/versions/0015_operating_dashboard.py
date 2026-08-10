"""AI operating committee and CEO dashboard foundation.

Revision ID: 0015_operating_dashboard
Revises: 0014_cfo_revenue
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0015_operating_dashboard"
down_revision: str | None = "0014_cfo_revenue"
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


def org() -> sa.ForeignKeyConstraint:
    return sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"])


def org_index(table: str) -> None:
    op.create_index(f"ix_{table}_organization_id", table, ["organization_id"])


def upgrade() -> None:
    op.create_table(
        "executive_metric_snapshots",
        *common(),
        sa.Column("organization_id", uuid, nullable=False),
        sa.Column("metric_type", sa.String(30), nullable=False),
        sa.Column("metric_name", sa.String(160), nullable=False),
        sa.Column("value", sa.Float(), nullable=False),
        sa.Column("unit", sa.String(40), nullable=False),
        sa.Column("source_domain", sa.String(30), nullable=False),
        sa.Column("period_id", uuid, nullable=False),
        org(),
        sa.ForeignKeyConstraint(["period_id"], ["financial_periods.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    org_index("executive_metric_snapshots")
    op.create_index(
        "ix_executive_metric_snapshots_period_id", "executive_metric_snapshots", ["period_id"]
    )
    op.create_table(
        "operating_signals",
        *common(),
        sa.Column("organization_id", uuid, nullable=False),
        sa.Column("domain", sa.String(30), nullable=False),
        sa.Column("severity", sa.String(20), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("impact", sa.Text(), nullable=False),
        sa.Column("recommendation", sa.Text(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        org(),
        sa.PrimaryKeyConstraint("id"),
    )
    org_index("operating_signals")
    op.create_table(
        "decision_queue_items",
        *common(),
        sa.Column("organization_id", uuid, nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("domain", sa.String(30), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("priority", sa.String(20), nullable=False),
        sa.Column("required_action", sa.String(20), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("approval_request_id", uuid),
        org(),
        sa.ForeignKeyConstraint(["approval_request_id"], ["approval_requests.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    org_index("decision_queue_items")
    op.create_table(
        "operating_committee_reviews",
        *common(),
        sa.Column("organization_id", uuid, nullable=False),
        sa.Column("period_id", uuid, nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("key_findings", sa.JSON(), nullable=False),
        sa.Column("risks", sa.JSON(), nullable=False),
        sa.Column("recommended_actions", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.CheckConstraint("confidence BETWEEN 0 AND 1", name="confidence_range"),
        org(),
        sa.ForeignKeyConstraint(["period_id"], ["financial_periods.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    org_index("operating_committee_reviews")
    op.create_index(
        "ix_operating_committee_reviews_period_id", "operating_committee_reviews", ["period_id"]
    )


def downgrade() -> None:
    for table in (
        "operating_committee_reviews",
        "decision_queue_items",
        "operating_signals",
        "executive_metric_snapshots",
    ):
        op.drop_table(table)
