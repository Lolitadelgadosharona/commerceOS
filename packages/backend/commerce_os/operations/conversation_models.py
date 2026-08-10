from datetime import datetime
from enum import StrEnum
from uuid import UUID

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column

from commerce_os.shared.database import Base
from commerce_os.shared.models import IdMixin, TimestampMixin, VersionMixin


class ThreadStatus(StrEnum):
    OPEN = "open"
    WAITING = "waiting"
    RESOLVED = "resolved"
    ESCALATED = "escalated"
    ARCHIVED = "archived"


class ConversationThread(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "conversation_threads"

    organization_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id"), nullable=False, index=True
    )
    customer_id: Mapped[UUID | None] = mapped_column(Uuid, ForeignKey("customers.id"))
    channel: Mapped[str] = mapped_column(String(30), nullable=False)
    status: Mapped[ThreadStatus] = mapped_column(String(30), nullable=False)
    priority: Mapped[str] = mapped_column(String(20), nullable=False)
    assigned_role_id: Mapped[UUID | None] = mapped_column(Uuid, ForeignKey("roles.id"))


class ConversationMessage(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "conversation_messages"
    __table_args__ = (UniqueConstraint("thread_id", "sequence"),)

    organization_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id"), nullable=False, index=True
    )
    thread_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("conversation_threads.id", ondelete="CASCADE"), nullable=False, index=True
    )
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    direction: Mapped[str] = mapped_column(String(20), nullable=False)
    sender_type: Mapped[str] = mapped_column(String(20), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)


class ConversationIntent(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "conversation_intents"
    __table_args__ = (CheckConstraint("confidence BETWEEN 0 AND 1", name="confidence_range"),)

    organization_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id"), nullable=False, index=True
    )
    message_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("conversation_messages.id", ondelete="CASCADE"), nullable=False, index=True
    )
    intent_type: Mapped[str] = mapped_column(String(40), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)


class ConversationEmotionSignal(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "conversation_emotion_signals"
    __table_args__ = (CheckConstraint("confidence BETWEEN 0 AND 1", name="confidence_range"),)

    organization_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id"), nullable=False, index=True
    )
    message_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("conversation_messages.id", ondelete="CASCADE"), nullable=False, index=True
    )
    emotion: Mapped[str] = mapped_column(String(30), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)


class ConversationHandoff(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "conversation_handoffs"

    organization_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id"), nullable=False, index=True
    )
    thread_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("conversation_threads.id", ondelete="CASCADE"), nullable=False, index=True
    )
    reason: Mapped[str] = mapped_column(String(40), nullable=False)
    priority: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False)
    assigned_user_id: Mapped[UUID | None] = mapped_column(Uuid, ForeignKey("users.id"))
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class ConversationKnowledgeReference(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "conversation_knowledge_references"
    __table_args__ = (UniqueConstraint("thread_id", "reference_type", "reference_id"),)

    organization_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id"), nullable=False, index=True
    )
    thread_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("conversation_threads.id", ondelete="CASCADE"), nullable=False, index=True
    )
    reference_type: Mapped[str] = mapped_column(String(40), nullable=False)
    reference_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
