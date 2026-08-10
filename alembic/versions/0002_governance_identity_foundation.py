"""Governance and identity foundation.

Revision ID: 0002_governance_identity
Revises: 0001_sprint_001
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0002_governance_identity"
down_revision: str | None = "0001_sprint_001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

uuid = sa.Uuid()


def timestamps(*, versioned: bool = True) -> list[sa.Column]:
    columns = [
        sa.Column("id", uuid, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    ]
    if versioned:
        columns.append(sa.Column("version", sa.Integer(), nullable=False))
    return columns


def upgrade() -> None:
    op.create_table(
        "users",
        *timestamps(),
        sa.Column("organization_id", uuid, nullable=False),
        sa.Column("email", sa.String(320), nullable=False),
        sa.Column("display_name", sa.String(200), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("principal_type", sa.String(30), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("organization_id", "email"),
    )
    op.create_index("ix_users_organization_id", "users", ["organization_id"])
    op.create_table(
        "password_credentials",
        *timestamps(),
        sa.Column("user_id", uuid, nullable=False),
        sa.Column("password_hash", sa.Text(), nullable=False),
        sa.Column("algorithm", sa.String(50), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id"),
    )
    op.create_table(
        "roles",
        *timestamps(),
        sa.Column("organization_id", uuid, nullable=False),
        sa.Column("name", sa.String(50), nullable=False),
        sa.Column("description", sa.String(500), nullable=False),
        sa.Column("grants_human_approval_authority", sa.Boolean(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("organization_id", "name"),
    )
    op.create_index("ix_roles_organization_id", "roles", ["organization_id"])
    op.create_table(
        "permissions",
        *timestamps(),
        sa.Column("key", sa.String(150), nullable=False),
        sa.Column("resource", sa.String(100), nullable=False),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("description", sa.String(500), nullable=False),
        sa.Column("is_human_approval_permission", sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("key"),
    )
    op.create_table(
        "role_permissions",
        *timestamps(versioned=False),
        sa.Column("role_id", uuid, nullable=False),
        sa.Column("permission_id", uuid, nullable=False),
        sa.ForeignKeyConstraint(["permission_id"], ["permissions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["role_id"], ["roles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("role_id", "permission_id"),
    )
    op.create_index("ix_role_permissions_permission_id", "role_permissions", ["permission_id"])
    op.create_index("ix_role_permissions_role_id", "role_permissions", ["role_id"])
    op.create_table(
        "user_roles",
        *timestamps(),
        sa.Column("user_id", uuid, nullable=False),
        sa.Column("role_id", uuid, nullable=False),
        sa.Column("organization_id", uuid, nullable=False),
        sa.Column("project_id", uuid),
        sa.Column("assigned_by", uuid, nullable=False),
        sa.Column("assigned_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True)),
        sa.Column("revoked_by", uuid),
        sa.Column("revocation_reason", sa.String(500)),
        sa.ForeignKeyConstraint(["assigned_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"]),
        sa.ForeignKeyConstraint(["revoked_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["role_id"], ["roles.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_user_roles_active_scope", "user_roles", ["user_id", "organization_id", "project_id"]
    )
    op.create_index("ix_user_roles_organization_id", "user_roles", ["organization_id"])
    op.create_index("ix_user_roles_role_id", "user_roles", ["role_id"])
    op.create_index("ix_user_roles_user_id", "user_roles", ["user_id"])
    op.create_table(
        "approval_requests",
        *timestamps(),
        sa.Column("organization_id", uuid, nullable=False),
        sa.Column("project_id", uuid),
        sa.Column("requester_id", uuid, nullable=False),
        sa.Column("object_type", sa.String(100), nullable=False),
        sa.Column("object_id", uuid, nullable=False),
        sa.Column("requested_action", sa.String(150), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("approver_id", uuid),
        sa.Column("decision_time", sa.DateTime(timezone=True)),
        sa.Column("decision_reason", sa.Text()),
        sa.ForeignKeyConstraint(["approver_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"]),
        sa.ForeignKeyConstraint(["requester_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_approval_requests_organization_id", "approval_requests", ["organization_id"]
    )
    op.create_index(
        "ix_approval_requests_scope_status", "approval_requests", ["organization_id", "status"]
    )
    op.create_table(
        "audit_logs",
        sa.Column("id", uuid, nullable=False),
        sa.Column("organization_id", uuid, nullable=False),
        sa.Column("actor_type", sa.String(30), nullable=False),
        sa.Column("actor_id", uuid),
        sa.Column("action", sa.String(150), nullable=False),
        sa.Column("entity_type", sa.String(100), nullable=False),
        sa.Column("entity_id", uuid, nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("metadata", sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_audit_logs_entity", "audit_logs", ["organization_id", "entity_type", "entity_id"]
    )
    op.create_index("ix_audit_logs_organization_id", "audit_logs", ["organization_id"])
    op.create_index("ix_audit_logs_timestamp", "audit_logs", ["timestamp"])

    with op.batch_alter_table("customer_identities") as batch:
        batch.add_column(sa.Column("provider", sa.String(50), nullable=True))
        batch.add_column(sa.Column("external_identifier", sa.String(320), nullable=True))
        batch.add_column(sa.Column("confidence_score", sa.Float(), nullable=True))
        batch.add_column(sa.Column("verification_status", sa.String(30), nullable=True))
    op.execute(
        "UPDATE customer_identities SET provider = source, external_identifier = normalized_value, "
        "confidence_score = confidence, verification_status = "
        "CASE WHEN link_status = 'verified' THEN 'verified' ELSE 'unverified' END"
    )
    with op.batch_alter_table("customer_identities") as batch:
        batch.alter_column("provider", existing_type=sa.String(50), nullable=False)
        batch.alter_column("external_identifier", existing_type=sa.String(320), nullable=False)
        batch.alter_column("confidence_score", existing_type=sa.Float(), nullable=False)
        batch.alter_column("verification_status", existing_type=sa.String(30), nullable=False)
        batch.create_unique_constraint(
            "uq_customer_identity_provider",
            ["organization_id", "provider", "external_identifier"],
        )


def downgrade() -> None:
    with op.batch_alter_table("customer_identities") as batch:
        batch.drop_constraint("uq_customer_identity_provider", type_="unique")
        batch.drop_column("verification_status")
        batch.drop_column("confidence_score")
        batch.drop_column("external_identifier")
        batch.drop_column("provider")
    for table in (
        "audit_logs",
        "approval_requests",
        "user_roles",
        "role_permissions",
        "permissions",
        "roles",
        "password_credentials",
        "users",
    ):
        op.drop_table(table)
