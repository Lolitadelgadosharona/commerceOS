"""Governed Shopify connection, publication, external state, and reconciliation.

Revision ID: 0076_shopify_channel_adapter
Revises: 0075_listing_intelligence
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0076_shopify_channel_adapter"
down_revision: str | None = "0075_listing_intelligence"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "shopify_connections",
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("store_id", sa.Uuid(), nullable=True),
        sa.Column("store_domain", sa.String(255), nullable=False),
        sa.Column("display_name", sa.String(255), nullable=False),
        sa.Column("authentication_mode", sa.String(30), nullable=False),
        sa.Column("credential_reference", sa.String(200), nullable=False),
        sa.Column("required_scopes", sa.JSON(), nullable=False),
        sa.Column("granted_scopes", sa.JSON(), nullable=False),
        sa.Column("api_version", sa.String(20), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("publication_policy", sa.JSON(), nullable=False),
        sa.Column("created_by", sa.Uuid(), nullable=False),
        sa.Column("validated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_error_category", sa.String(50), nullable=True),
        sa.Column("last_error_message", sa.Text(), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["store_id"], ["stores.id"]),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("organization_id", "store_domain"),
    )
    op.create_index(
        "ix_shopify_connections_organization_id", "shopify_connections", ["organization_id"]
    )
    op.create_index("ix_shopify_connections_store_id", "shopify_connections", ["store_id"])
    op.create_table(
        "shopify_publications",
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("connection_id", sa.Uuid(), nullable=False),
        sa.Column("product_id", sa.Uuid(), nullable=False),
        sa.Column("product_truth_id", sa.Uuid(), nullable=False),
        sa.Column("product_truth_version", sa.Integer(), nullable=False),
        sa.Column("listing_version_id", sa.Uuid(), nullable=False),
        sa.Column("listing_version", sa.Integer(), nullable=False),
        sa.Column("projection", sa.JSON(), nullable=False),
        sa.Column("projection_hash", sa.String(64), nullable=False),
        sa.Column("operation", sa.String(20), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("approval_request_id", sa.Uuid(), nullable=True),
        sa.Column("idempotency_key", sa.String(255), nullable=False),
        sa.Column("requested_by", sa.Uuid(), nullable=False),
        sa.Column("authorized_by", sa.Uuid(), nullable=True),
        sa.Column("authorized_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("execution_requested_by", sa.Uuid(), nullable=True),
        sa.Column("executed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("attempts", sa.Integer(), nullable=False),
        sa.Column("last_error_category", sa.String(50), nullable=True),
        sa.Column("last_error_message", sa.Text(), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["connection_id"], ["shopify_connections.id"]),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"]),
        sa.ForeignKeyConstraint(["product_truth_id"], ["product_truth.id"]),
        sa.ForeignKeyConstraint(["listing_version_id"], ["listing_versions.id"]),
        sa.ForeignKeyConstraint(["approval_request_id"], ["approval_requests.id"]),
        sa.ForeignKeyConstraint(["requested_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["authorized_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["execution_requested_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("organization_id", "idempotency_key"),
        sa.UniqueConstraint("connection_id", "listing_version_id"),
    )
    for column in ("organization_id", "connection_id", "product_id", "listing_version_id"):
        op.create_index(f"ix_shopify_publications_{column}", "shopify_publications", [column])
    op.create_table(
        "shopify_external_resources",
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("connection_id", sa.Uuid(), nullable=False),
        sa.Column("product_id", sa.Uuid(), nullable=False),
        sa.Column("external_product_id", sa.String(255), nullable=False),
        sa.Column("external_variant_ids", sa.JSON(), nullable=False),
        sa.Column("external_status", sa.String(30), nullable=False),
        sa.Column("owned_fields_snapshot", sa.JSON(), nullable=False),
        sa.Column("external_hash", sa.String(64), nullable=False),
        sa.Column("source_listing_version_id", sa.Uuid(), nullable=False),
        sa.Column("last_publication_id", sa.Uuid(), nullable=False),
        sa.Column("last_synced_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("admin_reference", sa.String(500), nullable=True),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["connection_id"], ["shopify_connections.id"]),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"]),
        sa.ForeignKeyConstraint(["source_listing_version_id"], ["listing_versions.id"]),
        sa.ForeignKeyConstraint(["last_publication_id"], ["shopify_publications.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("organization_id", "connection_id", "product_id"),
    )
    for column in ("organization_id", "connection_id", "product_id"):
        op.create_index(
            f"ix_shopify_external_resources_{column}", "shopify_external_resources", [column]
        )
    op.create_table(
        "shopify_reconciliations",
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("connection_id", sa.Uuid(), nullable=False),
        sa.Column("product_id", sa.Uuid(), nullable=False),
        sa.Column("external_resource_id", sa.Uuid(), nullable=True),
        sa.Column("publication_id", sa.Uuid(), nullable=True),
        sa.Column("status", sa.String(40), nullable=False),
        sa.Column("commerce_hash", sa.String(64), nullable=True),
        sa.Column("external_hash", sa.String(64), nullable=True),
        sa.Column("differences", sa.JSON(), nullable=False),
        sa.Column("checked_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("checked_by", sa.Uuid(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["connection_id"], ["shopify_connections.id"]),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"]),
        sa.ForeignKeyConstraint(["external_resource_id"], ["shopify_external_resources.id"]),
        sa.ForeignKeyConstraint(["publication_id"], ["shopify_publications.id"]),
        sa.ForeignKeyConstraint(["checked_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    for column in ("organization_id", "connection_id", "product_id", "external_resource_id"):
        op.create_index(f"ix_shopify_reconciliations_{column}", "shopify_reconciliations", [column])
    op.create_table(
        "shopify_webhook_events",
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("connection_id", sa.Uuid(), nullable=False),
        sa.Column("webhook_id", sa.String(255), nullable=False),
        sa.Column("topic", sa.String(100), nullable=False),
        sa.Column("payload_hash", sa.String(64), nullable=False),
        sa.Column("signature_valid", sa.Boolean(), nullable=False),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["connection_id"], ["shopify_connections.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("connection_id", "webhook_id"),
    )
    op.create_index(
        "ix_shopify_webhook_events_organization_id", "shopify_webhook_events", ["organization_id"]
    )
    op.create_index(
        "ix_shopify_webhook_events_connection_id", "shopify_webhook_events", ["connection_id"]
    )


def downgrade() -> None:
    for table in (
        "shopify_webhook_events",
        "shopify_reconciliations",
        "shopify_external_resources",
        "shopify_publications",
        "shopify_connections",
    ):
        op.drop_table(table)
