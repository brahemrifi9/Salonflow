"""add whatsapp sessions table

Revision ID: e7b72fb1dbb3
Revises: 5f34dc5a8adf
Create Date: 2026-03-06 13:08:56.135469

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "e7b72fb1dbb3"
down_revision: Union[str, None] = "5f34dc5a8adf"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "whatsapp_sessions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("telefono", sa.String(length=32), nullable=False),
        sa.Column("state", sa.String(length=64), nullable=False, server_default="MENU"),
        sa.Column("data_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("last_message_id", sa.String(length=128), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        op.f("ix_whatsapp_sessions_id"),
        "whatsapp_sessions",
        ["id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_whatsapp_sessions_telefono"),
        "whatsapp_sessions",
        ["telefono"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_whatsapp_sessions_telefono"), table_name="whatsapp_sessions")
    op.drop_index(op.f("ix_whatsapp_sessions_id"), table_name="whatsapp_sessions")
    op.drop_table("whatsapp_sessions")