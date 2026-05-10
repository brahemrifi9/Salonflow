"""add business hours columns to businesses

Revision ID: a005_add_business_hours
Revises: a004_business_id_not_null
Create Date: 2026-05-10 00:00:00

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a005_add_business_hours"
down_revision: Union[str, None] = "a004_business_id_not_null"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("businesses", sa.Column("open_time", sa.Time(), nullable=False, server_default="11:00"))
    op.add_column("businesses", sa.Column("close_time", sa.Time(), nullable=False, server_default="21:30"))
    op.add_column("businesses", sa.Column("lunch_start", sa.Time(), nullable=False, server_default="15:00"))
    op.add_column("businesses", sa.Column("lunch_end", sa.Time(), nullable=False, server_default="16:00"))


def downgrade() -> None:
    op.drop_column("businesses", "lunch_end")
    op.drop_column("businesses", "lunch_start")
    op.drop_column("businesses", "close_time")
    op.drop_column("businesses", "open_time")
