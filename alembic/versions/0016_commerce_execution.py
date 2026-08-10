"""Commerce execution and launch workflow foundation.

Revision ID: 0016_commerce_execution
Revises: 0015_operating_dashboard
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0016_commerce_execution"
down_revision: str | None = "0015_operating_dashboard"
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


def org() -> sa.ForeignKeyConstraint:
    return sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"])


def indexes(table: str, reference: str | None = None) -> None:
    op.create_index(f"ix_{table}_organization_id", table, ["organization_id"])
    if reference:
        op.create_index(f"ix_{table}_{reference}", table, [reference])


def upgrade() -> None:
    op.create_table(
        "product_launches",
        *common(),
        sa.Column("organization_id", uuid, nullable=False),
        sa.Column("project_id", uuid, nullable=False),
        sa.Column("product_id", uuid, nullable=False),
        sa.Column("market", sa.String(120), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("priority", sa.String(20), nullable=False),
        sa.Column("approval_request_id", uuid),
        org(),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"]),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"]),
        sa.ForeignKeyConstraint(["approval_request_id"], ["approval_requests.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    indexes("product_launches", "project_id")
    op.create_index("ix_product_launches_product_id", "product_launches", ["product_id"])
    op.create_table(
        "launch_milestones",
        *common(),
        sa.Column("organization_id", uuid, nullable=False),
        sa.Column("launch_id", uuid, nullable=False),
        sa.Column("name", sa.String(60), nullable=False),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("due_date", sa.Date()),
        sa.Column("owner_role_id", uuid),
        org(),
        sa.ForeignKeyConstraint(["launch_id"], ["product_launches.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["owner_role_id"], ["roles.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("launch_id", "sequence"),
    )
    indexes("launch_milestones", "launch_id")
    op.create_table(
        "execution_tasks",
        *common(),
        sa.Column("organization_id", uuid, nullable=False),
        sa.Column("launch_id", uuid, nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("owner_type", sa.String(20), nullable=False),
        sa.Column("priority", sa.String(20), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        org(),
        sa.ForeignKeyConstraint(["launch_id"], ["product_launches.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    indexes("execution_tasks", "launch_id")
    op.create_table(
        "action_plans",
        *common(),
        sa.Column("organization_id", uuid, nullable=False),
        sa.Column("plan_date", sa.Date(), nullable=False),
        sa.Column("related_launch_id", uuid, nullable=False),
        sa.Column("priority", sa.String(20), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("generated_from", sa.String(120), nullable=False),
        org(),
        sa.ForeignKeyConstraint(["related_launch_id"], ["product_launches.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    indexes("action_plans", "related_launch_id")
    op.create_table(
        "execution_blockers",
        *common(),
        sa.Column("organization_id", uuid, nullable=False),
        sa.Column("launch_id", uuid, nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("severity", sa.String(20), nullable=False),
        sa.Column("impact", sa.Text(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        org(),
        sa.ForeignKeyConstraint(["launch_id"], ["product_launches.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    indexes("execution_blockers", "launch_id")


def downgrade() -> None:
    for table in (
        "execution_blockers",
        "action_plans",
        "execution_tasks",
        "launch_milestones",
        "product_launches",
    ):
        op.drop_table(table)
