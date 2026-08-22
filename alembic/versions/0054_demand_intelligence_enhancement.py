"""Demand intelligence enhancement foundation.

Revision ID: 0054_demand_enhancement
Revises: 0053_business_demand
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0054_demand_enhancement"
down_revision: str | None = "0053_business_demand"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def common() -> list[sa.Column]:
    return [
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
    ]


def indexed(table: str, columns: list[str]) -> None:
    for column in columns:
        op.create_index(op.f(f"ix_{table}_{column}"), table, [column])


def upgrade() -> None:
    with op.batch_alter_table("demand_signal_sources") as batch:
        batch.add_column(
            sa.Column(
                "source_category",
                sa.String(40),
                nullable=False,
                server_default=sa.text("'customer_voice'"),
            )
        )
        batch.add_column(sa.Column("geographic_scope", sa.String(200)))
        batch.add_column(sa.Column("time_window", sa.String(120)))
        batch.add_column(sa.Column("trend_type", sa.String(40)))
    with op.batch_alter_table("demand_signal_sources") as batch:
        batch.alter_column("source_category", server_default=None)

    op.create_table(
        "predictive_demand_metadata",
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("demand_signal_id", sa.Uuid(), nullable=False),
        sa.Column("prediction_type", sa.String(80), nullable=False),
        sa.Column("forecast_window", sa.String(120), nullable=False),
        sa.Column("confidence_score", sa.Float(), nullable=False),
        sa.Column("assumptions", sa.JSON(), nullable=False),
        sa.Column("uncertainty_notes", sa.Text(), nullable=False),
        *common(),
        sa.CheckConstraint(
            "confidence_score BETWEEN 0 AND 1",
            name=op.f("ck_predictive_demand_metadata_confidence_range"),
        ),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["demand_signal_id"], ["demand_signals.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("demand_signal_id"),
    )
    indexed("predictive_demand_metadata", ["organization_id", "demand_signal_id"])

    op.create_table(
        "demand_theme_analyses",
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("category", sa.String(80), nullable=False),
        sa.Column("evidence_count", sa.Integer(), nullable=False),
        sa.Column("signal_diversity", sa.Integer(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("evidence_strength", sa.String(20), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        *common(),
        sa.CheckConstraint(
            "confidence BETWEEN 0 AND 1",
            name=op.f("ck_demand_theme_analyses_confidence_range"),
        ),
        sa.CheckConstraint(
            "evidence_count > 0",
            name=op.f("ck_demand_theme_analyses_positive_evidence_count"),
        ),
        sa.CheckConstraint(
            "signal_diversity > 0",
            name=op.f("ck_demand_theme_analyses_positive_signal_diversity"),
        ),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    indexed("demand_theme_analyses", ["organization_id"])

    op.create_table(
        "demand_theme_signal_links",
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("theme_analysis_id", sa.Uuid(), nullable=False),
        sa.Column("demand_signal_id", sa.Uuid(), nullable=False),
        *common(),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(
            ["theme_analysis_id"], ["demand_theme_analyses.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["demand_signal_id"], ["demand_signals.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("theme_analysis_id", "demand_signal_id"),
    )
    indexed(
        "demand_theme_signal_links",
        ["organization_id", "theme_analysis_id", "demand_signal_id"],
    )

    if op.get_context().dialect.name == "postgresql":
        op.execute(
            """
            CREATE FUNCTION prevent_demand_analysis_evidence_mutation() RETURNS trigger AS $$
            BEGIN RAISE EXCEPTION 'Demand analysis evidence is append-only'; END;
            $$ LANGUAGE plpgsql;
            CREATE TRIGGER predictive_demand_metadata_append_only
            BEFORE UPDATE OR DELETE ON predictive_demand_metadata
            FOR EACH ROW EXECUTE FUNCTION prevent_demand_analysis_evidence_mutation();
            CREATE TRIGGER demand_theme_signal_links_append_only
            BEFORE UPDATE OR DELETE ON demand_theme_signal_links
            FOR EACH ROW EXECUTE FUNCTION prevent_demand_analysis_evidence_mutation();
            """
        )


def downgrade() -> None:
    if op.get_context().dialect.name == "postgresql":
        op.execute(
            "DROP TRIGGER IF EXISTS demand_theme_signal_links_append_only "
            "ON demand_theme_signal_links"
        )
        op.execute(
            "DROP TRIGGER IF EXISTS predictive_demand_metadata_append_only "
            "ON predictive_demand_metadata"
        )
        op.execute("DROP FUNCTION IF EXISTS prevent_demand_analysis_evidence_mutation()")
    for table, columns in [
        (
            "demand_theme_signal_links",
            ["demand_signal_id", "theme_analysis_id", "organization_id"],
        ),
        ("demand_theme_analyses", ["organization_id"]),
        ("predictive_demand_metadata", ["demand_signal_id", "organization_id"]),
    ]:
        for column in columns:
            op.drop_index(op.f(f"ix_{table}_{column}"), table_name=table)
        op.drop_table(table)
    with op.batch_alter_table("demand_signal_sources") as batch:
        for column in ["trend_type", "time_window", "geographic_scope", "source_category"]:
            batch.drop_column(column)
