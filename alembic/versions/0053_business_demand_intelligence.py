"""Unified business demand intelligence foundation.

Revision ID: 0053_business_demand
Revises: 0052_demand_bridge
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0053_business_demand"
down_revision: str | None = "0052_demand_bridge"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "demand_signal_sources",
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("source_type", sa.String(80), nullable=False),
        sa.Column("display_name", sa.String(150), nullable=False),
        sa.Column("source_domain", sa.String(40), nullable=False),
        sa.Column("collection_method", sa.String(80), nullable=False),
        sa.Column("evidence_origin", sa.String(250), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("organization_id", "source_type"),
    )
    op.create_index(
        op.f("ix_demand_signal_sources_organization_id"),
        "demand_signal_sources",
        ["organization_id"],
    )

    with op.batch_alter_table("demand_signals") as batch:
        batch.add_column(
            sa.Column(
                "source_type",
                sa.String(80),
                nullable=False,
                server_default=sa.text("'growthos_conversation'"),
            )
        )
        batch.add_column(
            sa.Column(
                "source_reference",
                sa.String(500),
                nullable=False,
                server_default=sa.text("'legacy_growthos_reference'"),
            )
        )
        batch.add_column(
            sa.Column(
                "collection_method",
                sa.String(80),
                nullable=False,
                server_default=sa.text("'deterministic_aggregation'"),
            )
        )
        batch.add_column(
            sa.Column(
                "evidence_origin",
                sa.String(250),
                nullable=False,
                server_default=sa.text("'human_accepted_customer_conversation'"),
            )
        )
        batch.add_column(
            sa.Column(
                "confidence_basis",
                sa.Text(),
                nullable=False,
                server_default=sa.text("'Legacy Sprint 052 accepted learning confidence.'"),
            )
        )
        batch.create_index(op.f("ix_demand_signals_source_type"), ["source_type"])
    with op.batch_alter_table("demand_signals") as batch:
        for column in [
            "source_type",
            "source_reference",
            "collection_method",
            "evidence_origin",
            "confidence_basis",
        ]:
            batch.alter_column(column, server_default=None)

    with op.batch_alter_table("demand_signal_evidence") as batch:
        batch.add_column(
            sa.Column(
                "source_reference",
                sa.String(500),
                nullable=False,
                server_default=sa.text("'legacy_growthos_reference'"),
            )
        )
    with op.batch_alter_table("demand_signal_evidence") as batch:
        batch.alter_column("source_reference", server_default=None)


def downgrade() -> None:
    with op.batch_alter_table("demand_signal_evidence") as batch:
        batch.drop_column("source_reference")
    with op.batch_alter_table("demand_signals") as batch:
        batch.drop_index(op.f("ix_demand_signals_source_type"))
        for column in [
            "confidence_basis",
            "evidence_origin",
            "collection_method",
            "source_reference",
            "source_type",
        ]:
            batch.drop_column(column)
    op.drop_index(
        op.f("ix_demand_signal_sources_organization_id"),
        table_name="demand_signal_sources",
    )
    op.drop_table("demand_signal_sources")
