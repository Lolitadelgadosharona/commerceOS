from datetime import datetime
from enum import StrEnum
from uuid import UUID

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column

from commerce_os.shared.database import Base
from commerce_os.shared.models import IdMixin, TimestampMixin, VersionMixin


class Organization(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "organizations"

    name: Mapped[str] = mapped_column(String(200), unique=True, nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class Project(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "projects"
    __table_args__ = (UniqueConstraint("organization_id", "slug"),)

    organization_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="active", nullable=False)


class CustomerIdentity(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "customer_identities"
    __table_args__ = (
        UniqueConstraint(
            "organization_id",
            "provider",
            "external_identifier",
            name="uq_customer_identity_provider",
        ),
    )

    organization_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id"), nullable=False, index=True
    )
    customer_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("customers.id"), nullable=False, index=True
    )
    identity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    normalized_value: Mapped[str] = mapped_column(String(320), nullable=False)
    source: Mapped[str] = mapped_column(String(100), nullable=False)
    provenance: Mapped[dict[str, object]] = mapped_column(JSON, default=dict, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    link_status: Mapped[str] = mapped_column(String(30), default="observed", nullable=False)
    provider: Mapped[str] = mapped_column(String(50), nullable=False)
    external_identifier: Mapped[str] = mapped_column(String(320), nullable=False)
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False)
    verification_status: Mapped[str] = mapped_column(
        String(30), default="unverified", nullable=False
    )


class Approval(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "approvals"

    organization_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id"), nullable=False, index=True
    )
    action_type: Mapped[str] = mapped_column(String(100), nullable=False)
    subject_type: Mapped[str] = mapped_column(String(100), nullable=False)
    subject_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="requested", nullable=False)
    requested_by: Mapped[str] = mapped_column(String(200), nullable=False)
    decided_by: Mapped[str | None] = mapped_column(String(200))
    policy_version: Mapped[str] = mapped_column(String(50), nullable=False)
    reason: Mapped[str | None] = mapped_column(Text)
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    idempotency_key: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)


class CommercialPolicy(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "commercial_policies"
    __table_args__ = (UniqueConstraint("organization_id", "policy_key", "policy_version"),)

    organization_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id"), nullable=False, index=True
    )
    policy_key: Mapped[str] = mapped_column(String(100), nullable=False)
    policy_version: Mapped[str] = mapped_column(String(50), nullable=False)
    rules: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    effective_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class PrincipalType(StrEnum):
    HUMAN = "human"
    SERVICE = "service"


class UserStatus(StrEnum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    DISABLED = "disabled"


class User(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "users"
    __table_args__ = (UniqueConstraint("organization_id", "email"),)

    organization_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id"), nullable=False, index=True
    )
    email: Mapped[str] = mapped_column(String(320), nullable=False)
    display_name: Mapped[str] = mapped_column(String(200), nullable=False)
    status: Mapped[UserStatus] = mapped_column(
        String(30), default=UserStatus.ACTIVE, nullable=False
    )
    principal_type: Mapped[PrincipalType] = mapped_column(
        String(30), default=PrincipalType.HUMAN, nullable=False
    )


class PasswordCredential(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "password_credentials"

    user_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    algorithm: Mapped[str] = mapped_column(String(50), default="argon2id", nullable=False)


class Role(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "roles"
    __table_args__ = (UniqueConstraint("organization_id", "name"),)

    organization_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str] = mapped_column(String(500), default="", nullable=False)
    grants_human_approval_authority: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class Permission(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "permissions"

    key: Mapped[str] = mapped_column(String(150), unique=True, nullable=False)
    resource: Mapped[str] = mapped_column(String(100), nullable=False)
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(String(500), default="", nullable=False)
    is_human_approval_permission: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )


class AIActionPolicy(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "ai_action_policies"
    __table_args__ = (UniqueConstraint("organization_id", "action_type"),)

    organization_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id"), nullable=False, index=True
    )
    action_type: Mapped[str] = mapped_column(String(50), nullable=False)
    allowed: Mapped[bool] = mapped_column(Boolean, nullable=False)
    requires_approval: Mapped[bool] = mapped_column(Boolean, nullable=False)
    domain: Mapped[str] = mapped_column(String(30), nullable=False)


class RolePermission(IdMixin, TimestampMixin, Base):
    __tablename__ = "role_permissions"
    __table_args__ = (UniqueConstraint("role_id", "permission_id"),)

    role_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("roles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    permission_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("permissions.id", ondelete="CASCADE"), nullable=False, index=True
    )


class UserRole(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "user_roles"
    __table_args__ = (
        Index("ix_user_roles_active_scope", "user_id", "organization_id", "project_id"),
    )

    user_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    role_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("roles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    organization_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id"), nullable=False, index=True
    )
    project_id: Mapped[UUID | None] = mapped_column(Uuid, ForeignKey("projects.id"))
    assigned_by: Mapped[UUID] = mapped_column(Uuid, ForeignKey("users.id"), nullable=False)
    assigned_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    revoked_by: Mapped[UUID | None] = mapped_column(Uuid, ForeignKey("users.id"))
    revocation_reason: Mapped[str | None] = mapped_column(String(500))


class ApprovalStatus(StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


class ApprovalRequest(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "approval_requests"
    __table_args__ = (Index("ix_approval_requests_scope_status", "organization_id", "status"),)

    organization_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id"), nullable=False, index=True
    )
    project_id: Mapped[UUID | None] = mapped_column(Uuid, ForeignKey("projects.id"))
    requester_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("users.id"), nullable=False)
    object_type: Mapped[str] = mapped_column(String(100), nullable=False)
    object_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    requested_action: Mapped[str] = mapped_column(String(150), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[ApprovalStatus] = mapped_column(
        String(30), default=ApprovalStatus.PENDING, nullable=False
    )
    approver_id: Mapped[UUID | None] = mapped_column(Uuid, ForeignKey("users.id"))
    decision_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    decision_reason: Mapped[str | None] = mapped_column(Text)


class AuditLog(IdMixin, Base):
    __tablename__ = "audit_logs"
    __table_args__ = (
        Index("ix_audit_logs_entity", "organization_id", "entity_type", "entity_id"),
        Index("ix_audit_logs_timestamp", "timestamp"),
    )

    organization_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id"), nullable=False, index=True
    )
    actor_type: Mapped[str] = mapped_column(String(30), nullable=False)
    actor_id: Mapped[UUID | None] = mapped_column(Uuid)
    action: Mapped[str] = mapped_column(String(150), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(100), nullable=False)
    entity_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    event_metadata: Mapped[dict[str, object]] = mapped_column(
        "metadata", JSON, default=dict, nullable=False
    )
