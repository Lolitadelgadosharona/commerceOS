"""Customer 360 identity resolution foundation."""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0031_customer_360"
down_revision: str | None = "0030_channel_execution"
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
        "customer_identity_links",
        *common(),
        sa.Column("customer_id", uuid, nullable=False),
        sa.Column("identity_type", sa.String(30), nullable=False),
        sa.Column("external_reference", sa.String(500), nullable=False),
        sa.Column("source", sa.String(200), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.CheckConstraint("confidence BETWEEN 0 AND 1", name="confidence_range"),
        sa.ForeignKeyConstraint(["customer_id"], ["customers.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("organization_id", "identity_type", "external_reference", "source"),
        *base_constraints(),
    )
    indexes("customer_identity_links", ("organization_id", "customer_id"))

    op.create_table(
        "customer_journey_events",
        *common(),
        sa.Column("customer_id", uuid, nullable=False),
        sa.Column("identity_link_id", uuid, nullable=True),
        sa.Column("event_type", sa.String(), nullable=False),
        sa.Column("source", sa.String(), nullable=False),
        sa.Column("reference_id", sa.String(), nullable=False),
        sa.Column("metadata", sa.JSON(), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["customer_id"], ["customers.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["identity_link_id"], ["customer_identity_links.id"], ondelete="SET NULL"
        ),
        sa.UniqueConstraint("organization_id", "source", "reference_id", "event_type"),
        *base_constraints(),
    )
    indexes("customer_journey_events", ("organization_id", "customer_id", "identity_link_id"))

    op.create_table(
        "customer_360_profiles",
        *common(),
        sa.Column("customer_id", uuid, nullable=False),
        sa.Column("identity_count", sa.Integer(), nullable=False),
        sa.Column("conversation_count", sa.Integer(), nullable=False),
        sa.Column("journey_summary", sa.JSON(), nullable=False),
        sa.Column("risk_summary", sa.JSON(), nullable=False),
        sa.Column("value_summary", sa.JSON(), nullable=False),
        sa.Column("last_activity_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["customer_id"], ["customers.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("organization_id", "customer_id"),
        *base_constraints(),
    )
    indexes("customer_360_profiles", ("organization_id", "customer_id"))

    op.create_table(
        "customer_value_assessments",
        *common(),
        sa.Column("customer_id", uuid, nullable=False),
        sa.Column("revenue_indicator", sa.Float(), nullable=False),
        sa.Column("margin_indicator", sa.Float(), nullable=False),
        sa.Column("repeat_probability", sa.Float(), nullable=False),
        sa.Column("strategic_potential", sa.Float(), nullable=False),
        sa.Column("risk_indicator", sa.Float(), nullable=False),
        sa.Column("score", sa.Float(), nullable=False),
        sa.Column("formula_version", sa.String(50), nullable=False),
        sa.CheckConstraint("revenue_indicator BETWEEN 0 AND 100", name="revenue_range"),
        sa.CheckConstraint("margin_indicator BETWEEN 0 AND 100", name="margin_range"),
        sa.CheckConstraint("repeat_probability BETWEEN 0 AND 1", name="repeat_range"),
        sa.CheckConstraint("strategic_potential BETWEEN 0 AND 100", name="strategic_range"),
        sa.CheckConstraint("risk_indicator BETWEEN 0 AND 100", name="risk_range"),
        sa.CheckConstraint("score BETWEEN 0 AND 100", name="score_range"),
        sa.ForeignKeyConstraint(["customer_id"], ["customers.id"], ondelete="CASCADE"),
        *base_constraints(),
    )
    indexes("customer_value_assessments", ("organization_id", "customer_id"))


def downgrade() -> None:
    op.drop_table("customer_value_assessments")
    op.drop_table("customer_360_profiles")
    op.drop_table("customer_journey_events")
    op.drop_table("customer_identity_links")
