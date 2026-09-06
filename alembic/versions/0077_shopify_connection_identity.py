"""Persist safe Shopify merchant identity validation metadata.

Revision ID: 0077_shopify_connection_identity
Revises: 0076_shopify_channel_adapter
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0077_shopify_connection_identity"
down_revision: str | None = "0076_shopify_channel_adapter"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("shopify_connections", sa.Column("shop_gid", sa.String(255)))
    op.add_column("shopify_connections", sa.Column("merchant_name", sa.String(255)))
    op.add_column("shopify_connections", sa.Column("partner_development", sa.Boolean()))
    op.add_column("shopify_connections", sa.Column("plan_display_name", sa.String(100)))


def downgrade() -> None:
    op.drop_column("shopify_connections", "plan_display_name")
    op.drop_column("shopify_connections", "partner_development")
    op.drop_column("shopify_connections", "merchant_name")
    op.drop_column("shopify_connections", "shop_gid")
