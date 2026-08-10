"""Conversation commerce foundation.

Revision ID: 0011_conversation_commerce
Revises: 0010_channel_strategy
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0011_conversation_commerce"
down_revision: str | None = "0010_channel_strategy"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None
uuid = sa.Uuid()


def common() -> list[sa.Column]:
    return [
        sa.Column("id", uuid, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
    ]


def indexes(table: str, reference: str) -> None:
    op.create_index(f"ix_{table}_organization_id", table, ["organization_id"])
    op.create_index(f"ix_{table}_{reference}", table, [reference])


def org() -> sa.ForeignKeyConstraint:
    return sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"])


def upgrade() -> None:
    op.create_table(
        "conversation_threads",
        *common(),
        sa.Column("organization_id", uuid, nullable=False),
        sa.Column("customer_id", uuid),
        sa.Column("channel", sa.String(30), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("priority", sa.String(20), nullable=False),
        sa.Column("assigned_role_id", uuid),
        org(),
        sa.ForeignKeyConstraint(["customer_id"], ["customers.id"]),
        sa.ForeignKeyConstraint(["assigned_role_id"], ["roles.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_conversation_threads_organization_id", "conversation_threads", ["organization_id"]
    )
    op.create_table(
        "conversation_messages",
        *common(),
        sa.Column("organization_id", uuid, nullable=False),
        sa.Column("thread_id", uuid, nullable=False),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column("direction", sa.String(20), nullable=False),
        sa.Column("sender_type", sa.String(20), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        org(),
        sa.ForeignKeyConstraint(["thread_id"], ["conversation_threads.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("thread_id", "sequence"),
    )
    indexes("conversation_messages", "thread_id")
    for table, value_column, value_size in (
        ("conversation_intents", "intent_type", 40),
        ("conversation_emotion_signals", "emotion", 30),
    ):
        op.create_table(
            table,
            *common(),
            sa.Column("organization_id", uuid, nullable=False),
            sa.Column("message_id", uuid, nullable=False),
            sa.Column(value_column, sa.String(value_size), nullable=False),
            sa.Column("confidence", sa.Float(), nullable=False),
            sa.CheckConstraint("confidence BETWEEN 0 AND 1", name="confidence_range"),
            org(),
            sa.ForeignKeyConstraint(
                ["message_id"], ["conversation_messages.id"], ondelete="CASCADE"
            ),
            sa.PrimaryKeyConstraint("id"),
        )
        indexes(table, "message_id")
    op.create_table(
        "conversation_handoffs",
        *common(),
        sa.Column("organization_id", uuid, nullable=False),
        sa.Column("thread_id", uuid, nullable=False),
        sa.Column("reason", sa.String(40), nullable=False),
        sa.Column("priority", sa.String(20), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("assigned_user_id", uuid),
        sa.Column("resolved_at", sa.DateTime(timezone=True)),
        org(),
        sa.ForeignKeyConstraint(["thread_id"], ["conversation_threads.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["assigned_user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    indexes("conversation_handoffs", "thread_id")
    op.create_table(
        "conversation_knowledge_references",
        *common(),
        sa.Column("organization_id", uuid, nullable=False),
        sa.Column("thread_id", uuid, nullable=False),
        sa.Column("reference_type", sa.String(40), nullable=False),
        sa.Column("reference_id", uuid, nullable=False),
        org(),
        sa.ForeignKeyConstraint(["thread_id"], ["conversation_threads.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("thread_id", "reference_type", "reference_id"),
    )
    indexes("conversation_knowledge_references", "thread_id")


def downgrade() -> None:
    for table in (
        "conversation_knowledge_references",
        "conversation_handoffs",
        "conversation_emotion_signals",
        "conversation_intents",
        "conversation_messages",
        "conversation_threads",
    ):
        op.drop_table(table)
