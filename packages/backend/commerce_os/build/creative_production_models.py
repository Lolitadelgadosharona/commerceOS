from typing import Any
from uuid import UUID

from sqlalchemy import JSON, ForeignKey, String, Text, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from commerce_os.shared.database import Base
from commerce_os.shared.models import IdMixin, TimestampMixin, VersionMixin


class CreativeProductionRequest(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "creative_production_requests"

    organization_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id"), nullable=False, index=True
    )
    project_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("projects.id"), nullable=False, index=True
    )
    creative_brief_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("creative_briefs.id"), nullable=False, index=True
    )
    format: Mapped[str] = mapped_column(String(30), nullable=False)
    channel: Mapped[str] = mapped_column(String(50), nullable=False)
    audience: Mapped[str] = mapped_column(Text, nullable=False)
    objective: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    requested_by: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("users.id"), nullable=False, index=True
    )
    approval_state: Mapped[str] = mapped_column(String(20), nullable=False)
    approval_request_id: Mapped[UUID | None] = mapped_column(
        Uuid, ForeignKey("approval_requests.id"), index=True
    )


class CreativeProductionWork(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "creative_production_work"

    organization_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id"), nullable=False, index=True
    )
    production_request_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("creative_production_requests.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    work_type: Mapped[str] = mapped_column(String(30), nullable=False)
    title: Mapped[str] = mapped_column(String(250), nullable=False)
    content_metadata: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)


class CreativeProductionAIProvenance(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "creative_production_ai_provenance"
    __table_args__ = (UniqueConstraint("production_work_id", "ai_request_id"),)

    organization_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id"), nullable=False, index=True
    )
    production_request_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("creative_production_requests.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    production_work_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("creative_production_work.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    ai_request_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("ai_requests.id"), nullable=False, index=True
    )
    output_classification: Mapped[str] = mapped_column(String(30), nullable=False)
    output_metadata: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    provenance_note: Mapped[str] = mapped_column(Text, nullable=False)
