from decimal import Decimal
from enum import StrEnum
from typing import Any
from uuid import UUID

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    ForeignKey,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column

from commerce_os.shared.database import Base
from commerce_os.shared.models import IdMixin, TimestampMixin, VersionMixin


class AIRequestStatus(StrEnum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    APPROVED_IF_REQUIRED = "approved_if_required"
    READY = "ready"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AIOutputClassification(StrEnum):
    RECOMMENDATION = "recommendation"
    DRAFT = "draft"
    ANALYSIS = "analysis"
    CANDIDATE = "candidate"
    CLASSIFICATION = "classification"


class AIProvider(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "ai_providers"
    __table_args__ = (UniqueConstraint("organization_id", "provider_identity"),)

    organization_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("organizations.id"), index=True)
    provider_identity: Mapped[str] = mapped_column(String(150), nullable=False)
    display_name: Mapped[str] = mapped_column(String(200), nullable=False)
    availability_state: Mapped[str] = mapped_column(String(30), nullable=False)
    provider_version: Mapped[str] = mapped_column(String(100), nullable=False)
    cost_metadata: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)


class AIModelCapability(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "ai_model_capabilities"
    __table_args__ = (
        UniqueConstraint("organization_id", "provider_id", "model_identity", "capability_type"),
    )

    organization_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("organizations.id"), index=True)
    provider_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("ai_providers.id", ondelete="CASCADE"), index=True
    )
    model_identity: Mapped[str] = mapped_column(String(200), nullable=False)
    capability_type: Mapped[str] = mapped_column(String(40), nullable=False)
    model_version: Mapped[str] = mapped_column(String(100), nullable=False)
    available: Mapped[bool] = mapped_column(Boolean, nullable=False)
    cost_metadata: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)


class AIRequest(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "ai_requests"

    organization_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("organizations.id"), index=True)
    requester_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("users.id"), index=True)
    purpose: Mapped[str] = mapped_column(String(200), nullable=False)
    context_type: Mapped[str] = mapped_column(String(100), nullable=False)
    context_reference: Mapped[str] = mapped_column(String(500), nullable=False)
    capability_id: Mapped[UUID | None] = mapped_column(
        Uuid, ForeignKey("ai_model_capabilities.id"), index=True
    )
    approval_request_id: Mapped[UUID | None] = mapped_column(
        Uuid, ForeignKey("approval_requests.id"), index=True
    )
    status: Mapped[AIRequestStatus] = mapped_column(String(30), nullable=False)
    output_classification: Mapped[AIOutputClassification | None] = mapped_column(String(30))
    output_metadata: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    failure_reason: Mapped[str | None] = mapped_column(Text)


class PromptPurpose(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "prompt_purposes"
    __table_args__ = (UniqueConstraint("organization_id", "name"),)

    organization_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("organizations.id"), index=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    owning_domain: Mapped[str] = mapped_column(String(40), nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False)


class PromptTemplate(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "prompt_templates"
    __table_args__ = (UniqueConstraint("organization_id", "name"),)

    organization_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("organizations.id"), index=True)
    purpose_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("prompt_purposes.id"), index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    owner_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("users.id"), index=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False)


class PromptVersion(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "prompt_versions"
    __table_args__ = (UniqueConstraint("template_id", "version_number"),)

    organization_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("organizations.id"), index=True)
    template_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("prompt_templates.id", ondelete="CASCADE"), index=True
    )
    version_number: Mapped[int] = mapped_column(nullable=False)
    prompt_content: Mapped[str] = mapped_column(Text, nullable=False)
    configuration: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    created_by: Mapped[UUID] = mapped_column(Uuid, ForeignKey("users.id"), index=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False)


class PromptEvaluation(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "prompt_evaluations"
    __table_args__ = (
        CheckConstraint("score BETWEEN 0 AND 100", name="prompt_evaluation_score_range"),
    )

    organization_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("organizations.id"), index=True)
    prompt_version_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("prompt_versions.id", ondelete="CASCADE"), index=True
    )
    evaluator_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("users.id"), index=True)
    score: Mapped[float] = mapped_column(nullable=False)
    result: Mapped[str] = mapped_column(String(30), nullable=False)
    notes: Mapped[str] = mapped_column(Text, nullable=False)


class AICostObservation(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "ai_cost_observations"
    __table_args__ = (
        CheckConstraint("usage_quantity >= 0", name="ai_usage_quantity_nonnegative"),
        CheckConstraint("estimated_cost >= 0", name="ai_estimated_cost_nonnegative"),
    )

    organization_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("organizations.id"), index=True)
    provider_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("ai_providers.id"), index=True)
    capability_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("ai_model_capabilities.id"), index=True
    )
    usage_quantity: Mapped[Decimal] = mapped_column(Numeric(19, 6), nullable=False)
    usage_unit: Mapped[str] = mapped_column(String(50), nullable=False)
    estimated_cost: Mapped[Decimal] = mapped_column(Numeric(19, 6), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    project_id: Mapped[UUID | None] = mapped_column(Uuid, ForeignKey("projects.id"), index=True)
    related_request_id: Mapped[UUID | None] = mapped_column(
        Uuid, ForeignKey("ai_requests.id"), index=True
    )
