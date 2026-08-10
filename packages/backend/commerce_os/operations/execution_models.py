from datetime import date
from uuid import UUID

from sqlalchemy import Date, ForeignKey, Integer, String, Text, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from commerce_os.shared.database import Base
from commerce_os.shared.models import IdMixin, TimestampMixin, VersionMixin


class ProductLaunch(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "product_launches"

    organization_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id"), nullable=False, index=True
    )
    project_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("projects.id"), nullable=False, index=True
    )
    product_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("products.id"), nullable=False, index=True
    )
    market: Mapped[str] = mapped_column(String(120), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    priority: Mapped[str] = mapped_column(String(20), nullable=False)
    approval_request_id: Mapped[UUID | None] = mapped_column(
        Uuid, ForeignKey("approval_requests.id")
    )


class LaunchMilestone(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "launch_milestones"
    __table_args__ = (UniqueConstraint("launch_id", "sequence"),)

    organization_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id"), nullable=False, index=True
    )
    launch_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("product_launches.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(60), nullable=False)
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    due_date: Mapped[date | None] = mapped_column(Date)
    owner_role_id: Mapped[UUID | None] = mapped_column(Uuid, ForeignKey("roles.id"))


class ExecutionTask(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "execution_tasks"

    organization_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id"), nullable=False, index=True
    )
    launch_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("product_launches.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    owner_type: Mapped[str] = mapped_column(String(20), nullable=False)
    priority: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)


class ActionPlan(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "action_plans"

    organization_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id"), nullable=False, index=True
    )
    plan_date: Mapped[date] = mapped_column(Date, nullable=False)
    related_launch_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("product_launches.id", ondelete="CASCADE"), nullable=False, index=True
    )
    priority: Mapped[str] = mapped_column(String(20), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    generated_from: Mapped[str] = mapped_column(String(120), nullable=False)


class ExecutionBlocker(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "execution_blockers"

    organization_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id"), nullable=False, index=True
    )
    launch_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("product_launches.id", ondelete="CASCADE"), nullable=False, index=True
    )
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    severity: Mapped[str] = mapped_column(String(20), nullable=False)
    impact: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
