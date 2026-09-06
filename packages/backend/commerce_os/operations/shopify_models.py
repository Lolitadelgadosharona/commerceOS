from datetime import datetime
from uuid import UUID

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, String, Text, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from commerce_os.shared.database import Base
from commerce_os.shared.models import IdMixin, TimestampMixin, VersionMixin


class ShopifyConnection(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "shopify_connections"
    __table_args__ = (UniqueConstraint("organization_id", "store_domain"),)

    organization_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("organizations.id"), index=True)
    store_id: Mapped[UUID | None] = mapped_column(Uuid, ForeignKey("stores.id"), index=True)
    store_domain: Mapped[str] = mapped_column(String(255))
    display_name: Mapped[str] = mapped_column(String(255))
    authentication_mode: Mapped[str] = mapped_column(String(30), default="local_token")
    credential_reference: Mapped[str] = mapped_column(String(200))
    required_scopes: Mapped[list[str]] = mapped_column(JSON, default=list)
    granted_scopes: Mapped[list[str]] = mapped_column(JSON, default=list)
    api_version: Mapped[str] = mapped_column(String(20))
    status: Mapped[str] = mapped_column(String(30), default="not_configured")
    publication_policy: Mapped[dict[str, object]] = mapped_column(JSON, default=dict)
    created_by: Mapped[UUID] = mapped_column(Uuid, ForeignKey("users.id"))
    validated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    shop_gid: Mapped[str | None] = mapped_column(String(255))
    merchant_name: Mapped[str | None] = mapped_column(String(255))
    partner_development: Mapped[bool | None] = mapped_column(Boolean)
    plan_display_name: Mapped[str | None] = mapped_column(String(100))
    last_error_category: Mapped[str | None] = mapped_column(String(50))
    last_error_message: Mapped[str | None] = mapped_column(Text)


class ShopifyPublication(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "shopify_publications"
    __table_args__ = (
        UniqueConstraint("organization_id", "idempotency_key"),
        UniqueConstraint("connection_id", "listing_version_id"),
    )

    organization_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("organizations.id"), index=True)
    connection_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("shopify_connections.id"), index=True
    )
    product_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("products.id"), index=True)
    product_truth_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("product_truth.id"))
    product_truth_version: Mapped[int] = mapped_column()
    listing_version_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("listing_versions.id"), index=True
    )
    listing_version: Mapped[int] = mapped_column()
    projection: Mapped[dict[str, object]] = mapped_column(JSON)
    projection_hash: Mapped[str] = mapped_column(String(64))
    operation: Mapped[str] = mapped_column(String(20))
    status: Mapped[str] = mapped_column(String(30), default="requested")
    approval_request_id: Mapped[UUID | None] = mapped_column(
        Uuid, ForeignKey("approval_requests.id")
    )
    idempotency_key: Mapped[str] = mapped_column(String(255))
    requested_by: Mapped[UUID] = mapped_column(Uuid, ForeignKey("users.id"))
    authorized_by: Mapped[UUID | None] = mapped_column(Uuid, ForeignKey("users.id"))
    authorized_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    execution_requested_by: Mapped[UUID | None] = mapped_column(Uuid, ForeignKey("users.id"))
    executed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    attempts: Mapped[int] = mapped_column(default=0)
    last_error_category: Mapped[str | None] = mapped_column(String(50))
    last_error_message: Mapped[str | None] = mapped_column(Text)


class ShopifyExternalResource(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "shopify_external_resources"
    __table_args__ = (UniqueConstraint("organization_id", "connection_id", "product_id"),)

    organization_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("organizations.id"), index=True)
    connection_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("shopify_connections.id"), index=True
    )
    product_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("products.id"), index=True)
    external_product_id: Mapped[str] = mapped_column(String(255))
    external_variant_ids: Mapped[list[str]] = mapped_column(JSON, default=list)
    external_status: Mapped[str] = mapped_column(String(30), default="draft")
    owned_fields_snapshot: Mapped[dict[str, object]] = mapped_column(JSON)
    external_hash: Mapped[str] = mapped_column(String(64))
    source_listing_version_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("listing_versions.id"))
    last_publication_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("shopify_publications.id"))
    last_synced_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    admin_reference: Mapped[str | None] = mapped_column(String(500))
    active: Mapped[bool] = mapped_column(Boolean, default=True)


class ShopifyReconciliation(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "shopify_reconciliations"

    organization_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("organizations.id"), index=True)
    connection_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("shopify_connections.id"), index=True
    )
    product_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("products.id"), index=True)
    external_resource_id: Mapped[UUID | None] = mapped_column(
        Uuid, ForeignKey("shopify_external_resources.id"), index=True
    )
    publication_id: Mapped[UUID | None] = mapped_column(Uuid, ForeignKey("shopify_publications.id"))
    status: Mapped[str] = mapped_column(String(40))
    commerce_hash: Mapped[str | None] = mapped_column(String(64))
    external_hash: Mapped[str | None] = mapped_column(String(64))
    differences: Mapped[list[str]] = mapped_column(JSON, default=list)
    checked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    checked_by: Mapped[UUID] = mapped_column(Uuid, ForeignKey("users.id"))


class ShopifyWebhookEvent(IdMixin, TimestampMixin, Base):
    __tablename__ = "shopify_webhook_events"
    __table_args__ = (UniqueConstraint("connection_id", "webhook_id"),)

    organization_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("organizations.id"), index=True)
    connection_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("shopify_connections.id"), index=True
    )
    webhook_id: Mapped[str] = mapped_column(String(255))
    topic: Mapped[str] = mapped_column(String(100))
    payload_hash: Mapped[str] = mapped_column(String(64))
    signature_valid: Mapped[bool] = mapped_column(Boolean)
    processed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
