"""Sprint 001 foundation schema.

Revision ID: 0001_sprint_001
Revises: None
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0001_sprint_001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

uuid = sa.Uuid()


def timestamp_columns() -> list[sa.Column]:
    return [
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    ]


def common_columns() -> list[sa.Column]:
    return [
        sa.Column("id", uuid, nullable=False),
        *timestamp_columns(),
        sa.Column("version", sa.Integer(), nullable=False),
    ]


def upgrade() -> None:
    op.create_table(
        "organizations",
        *common_columns(),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("slug", sa.String(100), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
        sa.UniqueConstraint("slug"),
    )
    op.create_table(
        "projects",
        *common_columns(),
        sa.Column("organization_id", uuid, nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("slug", sa.String(100), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("organization_id", "slug"),
    )
    op.create_index("ix_projects_organization_id", "projects", ["organization_id"])
    op.create_table(
        "brands",
        *common_columns(),
        sa.Column("organization_id", uuid, nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("slug", sa.String(100), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("organization_id", "slug"),
    )
    op.create_index("ix_brands_organization_id", "brands", ["organization_id"])
    op.create_table(
        "stores",
        *common_columns(),
        sa.Column("organization_id", uuid, nullable=False),
        sa.Column("brand_id", uuid, nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("slug", sa.String(100), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.ForeignKeyConstraint(["brand_id"], ["brands.id"]),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("organization_id", "slug"),
    )
    op.create_index("ix_stores_organization_id", "stores", ["organization_id"])
    op.create_table(
        "customers",
        *common_columns(),
        sa.Column("organization_id", uuid, nullable=False),
        sa.Column("display_name", sa.String(200), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("attributes", sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_customers_organization_id", "customers", ["organization_id"])
    op.create_table(
        "venture_opportunities",
        *common_columns(),
        sa.Column("organization_id", uuid, nullable=False),
        sa.Column("project_id", uuid),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("thesis", sa.Text()),
        sa.Column("stage", sa.String(30), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_venture_opportunities_organization_id", "venture_opportunities", ["organization_id"]
    )
    op.create_table(
        "sales_opportunities",
        *common_columns(),
        sa.Column("organization_id", uuid, nullable=False),
        sa.Column("project_id", uuid),
        sa.Column("customer_id", uuid),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("stage", sa.String(30), nullable=False),
        sa.Column("owner_ref", sa.String(200)),
        sa.ForeignKeyConstraint(["customer_id"], ["customers.id"]),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_sales_opportunities_organization_id", "sales_opportunities", ["organization_id"]
    )
    op.create_table(
        "customer_identities",
        *common_columns(),
        sa.Column("organization_id", uuid, nullable=False),
        sa.Column("customer_id", uuid, nullable=False),
        sa.Column("identity_type", sa.String(50), nullable=False),
        sa.Column("normalized_value", sa.String(320), nullable=False),
        sa.Column("source", sa.String(100), nullable=False),
        sa.Column("provenance", sa.JSON(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("link_status", sa.String(30), nullable=False),
        sa.ForeignKeyConstraint(["customer_id"], ["customers.id"]),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_customer_identities_customer_id", "customer_identities", ["customer_id"])
    op.create_index(
        "ix_customer_identities_organization_id", "customer_identities", ["organization_id"]
    )
    op.create_table(
        "conversations",
        *common_columns(),
        sa.Column("organization_id", uuid, nullable=False),
        sa.Column("customer_id", uuid),
        sa.Column("channel", sa.String(50), nullable=False),
        sa.Column("purpose", sa.String(30), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("policy_version", sa.String(50), nullable=False),
        sa.Column("closed_at", sa.DateTime(timezone=True)),
        sa.ForeignKeyConstraint(["customer_id"], ["customers.id"]),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_conversations_organization_id", "conversations", ["organization_id"])
    op.create_table(
        "message_metadata",
        *common_columns(),
        sa.Column("conversation_id", uuid, nullable=False),
        sa.Column("direction", sa.String(20), nullable=False),
        sa.Column("external_message_id", sa.String(255)),
        sa.Column("content_reference", sa.Text()),
        sa.Column("content_hash", sa.String(128)),
        sa.Column("trust_classification", sa.String(30), nullable=False),
        sa.Column("delivery_status", sa.String(30), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["conversation_id"], ["conversations.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("conversation_id", "external_message_id"),
    )
    op.create_index("ix_message_metadata_conversation_id", "message_metadata", ["conversation_id"])
    op.create_table(
        "approvals",
        *common_columns(),
        sa.Column("organization_id", uuid, nullable=False),
        sa.Column("action_type", sa.String(100), nullable=False),
        sa.Column("subject_type", sa.String(100), nullable=False),
        sa.Column("subject_id", uuid, nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("requested_by", sa.String(200), nullable=False),
        sa.Column("decided_by", sa.String(200)),
        sa.Column("policy_version", sa.String(50), nullable=False),
        sa.Column("reason", sa.Text()),
        sa.Column("decided_at", sa.DateTime(timezone=True)),
        sa.Column("expires_at", sa.DateTime(timezone=True)),
        sa.Column("idempotency_key", sa.String(255), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("idempotency_key"),
    )
    op.create_index("ix_approvals_organization_id", "approvals", ["organization_id"])
    op.create_table(
        "commercial_policies",
        *common_columns(),
        sa.Column("organization_id", uuid, nullable=False),
        sa.Column("policy_key", sa.String(100), nullable=False),
        sa.Column("policy_version", sa.String(50), nullable=False),
        sa.Column("rules", sa.JSON(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("effective_at", sa.DateTime(timezone=True)),
        sa.Column("expires_at", sa.DateTime(timezone=True)),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("organization_id", "policy_key", "policy_version"),
    )
    op.create_index(
        "ix_commercial_policies_organization_id", "commercial_policies", ["organization_id"]
    )
    op.create_table(
        "outbox_events",
        sa.Column("id", uuid, nullable=False),
        *timestamp_columns(),
        sa.Column("event_id", uuid, nullable=False),
        sa.Column("event_type", sa.String(150), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("actor", sa.JSON(), nullable=False),
        sa.Column("source", sa.String(100), nullable=False),
        sa.Column("idempotency_key", sa.String(255), nullable=False),
        sa.Column("correlation_id", uuid, nullable=False),
        sa.Column("causation_id", uuid),
        sa.Column("organization_id", uuid, nullable=False),
        sa.Column("project_id", uuid),
        sa.Column("product_id", uuid),
        sa.Column("customer_id", uuid),
        sa.Column("schema_version", sa.Integer(), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(10), nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=False),
        sa.Column("available_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True)),
        sa.Column("last_error", sa.Text()),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("event_id"),
        sa.UniqueConstraint("organization_id", "idempotency_key"),
    )
    op.create_index("ix_outbox_events_organization_id", "outbox_events", ["organization_id"])
    op.create_index(
        "ix_outbox_events_status_occurred_at", "outbox_events", ["status", "occurred_at"]
    )


def downgrade() -> None:
    for table in (
        "outbox_events",
        "commercial_policies",
        "approvals",
        "message_metadata",
        "conversations",
        "customer_identities",
        "sales_opportunities",
        "venture_opportunities",
        "customers",
        "stores",
        "brands",
        "projects",
        "organizations",
    ):
        op.drop_table(table)
