"""create businesses table

Revision ID: a001_create_businesses
Revises: f526af576412
Create Date: 2026-03-28 00:00:01

SAFE: purely additive. No existing tables touched.
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "a001_create_businesses"
down_revision: Union[str, None] = "2ce7b3797fdc"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "businesses",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("country", sa.String(length=64), nullable=False, server_default="ES"),
        sa.Column("language", sa.String(length=8), nullable=False, server_default="es"),
        sa.Column("currency", sa.String(length=8), nullable=False, server_default="EUR"),
        sa.Column("timezone", sa.String(length=64), nullable=False, server_default="Europe/Madrid"),
        sa.Column("whatsapp_phone_number_id", sa.String(length=64), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_businesses_id"), "businesses", ["id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_businesses_id"), table_name="businesses")
    op.drop_table("businesses")
