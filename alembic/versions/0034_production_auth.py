"""Production authentication sessions."""

from collections.abc import Sequence
from datetime import UTC, datetime
from uuid import uuid4

import sqlalchemy as sa

from alembic import op

revision: str = "0034_production_auth"
down_revision: str | None = "0032_strategic_accounts"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    permissions = sa.table(
        "permissions",
        sa.column("id", sa.Uuid()),
        sa.column("key", sa.String()),
        sa.column("resource", sa.String()),
        sa.column("action", sa.String()),
        sa.column("description", sa.String()),
        sa.column("is_human_approval_permission", sa.Boolean()),
        sa.column("created_at", sa.DateTime(timezone=True)),
        sa.column("updated_at", sa.DateTime(timezone=True)),
        sa.column("version", sa.Integer()),
    )
    now = datetime.now(UTC)
    op.bulk_insert(
        permissions,
        [
            {
                "id": uuid4(),
                "key": "api.read",
                "resource": "api",
                "action": "read",
                "description": "Read protected API resources.",
                "is_human_approval_permission": False,
                "created_at": now,
                "updated_at": now,
                "version": 1,
            },
            {
                "id": uuid4(),
                "key": "api.write",
                "resource": "api",
                "action": "write",
                "description": "Mutate protected API resources.",
                "is_human_approval_permission": False,
                "created_at": now,
                "updated_at": now,
                "version": 1,
            },
        ],
    )
    op.create_table(
        "auth_sessions",
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("token_hash", sa.String(64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True)),
        sa.Column("last_used_at", sa.DateTime(timezone=True)),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_auth_sessions_organization_id", "auth_sessions", ["organization_id"])
    op.create_index("ix_auth_sessions_user_id", "auth_sessions", ["user_id"])
    op.create_index("ix_auth_sessions_token_hash", "auth_sessions", ["token_hash"], unique=True)


def downgrade() -> None:
    op.drop_table("auth_sessions")
    op.execute(sa.text("DELETE FROM permissions WHERE key IN ('api.read', 'api.write')"))
