from datetime import datetime
from uuid import UUID

from sqlalchemy import JSON, DateTime, ForeignKey, String, Text, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from commerce_os.shared.database import Base
from commerce_os.shared.models import IdMixin, TimestampMixin, VersionMixin


class Brand(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "brands"
    __table_args__ = (UniqueConstraint("organization_id", "slug"),)

    organization_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), nullable=False)


class Store(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "stores"
    __table_args__ = (UniqueConstraint("organization_id", "slug"),)

    organization_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id"), nullable=False, index=True
    )
    brand_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("brands.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="active", nullable=False)


class Customer(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "customers"

    organization_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id"), nullable=False, index=True
    )
    display_name: Mapped[str] = mapped_column(String(200), nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="active", nullable=False)
    attributes: Mapped[dict[str, object]] = mapped_column(JSON, default=dict, nullable=False)


class SalesOpportunity(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "sales_opportunities"

    organization_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id"), nullable=False, index=True
    )
    project_id: Mapped[UUID | None] = mapped_column(Uuid, ForeignKey("projects.id"))
    customer_id: Mapped[UUID | None] = mapped_column(Uuid, ForeignKey("customers.id"))
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    stage: Mapped[str] = mapped_column(String(30), default="created", nullable=False)
    owner_ref: Mapped[str | None] = mapped_column(String(200))


class Conversation(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "conversations"

    organization_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id"), nullable=False, index=True
    )
    customer_id: Mapped[UUID | None] = mapped_column(Uuid, ForeignKey("customers.id"))
    channel: Mapped[str] = mapped_column(String(50), nullable=False)
    purpose: Mapped[str] = mapped_column(String(30), nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="open", nullable=False)
    policy_version: Mapped[str] = mapped_column(String(50), nullable=False)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class MessageMetadata(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "message_metadata"
    __table_args__ = (UniqueConstraint("conversation_id", "external_message_id"),)

    conversation_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("conversations.id"), nullable=False, index=True
    )
    direction: Mapped[str] = mapped_column(String(20), nullable=False)
    external_message_id: Mapped[str | None] = mapped_column(String(255))
    content_reference: Mapped[str | None] = mapped_column(Text)
    content_hash: Mapped[str | None] = mapped_column(String(128))
    trust_classification: Mapped[str] = mapped_column(
        String(30), default="untrusted_external", nullable=False
    )
    delivery_status: Mapped[str] = mapped_column(String(30), default="received", nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
