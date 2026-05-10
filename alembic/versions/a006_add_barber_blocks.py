"""add barber_blocks table

Revision ID: a006_add_barber_blocks
Revises: a005_add_business_hours
Create Date: 2026-05-10 00:00:00

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a006_add_barber_blocks"
down_revision: Union[str, None] = "a005_add_business_hours"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "barber_blocks",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("business_id", sa.Integer(), sa.ForeignKey("businesses.id"), nullable=False),
        sa.Column("barber_id", sa.Integer(), sa.ForeignKey("barbers.id"), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("start_time", sa.Time(), nullable=False),
        sa.Column("end_time", sa.Time(), nullable=False),
        sa.Column("reason", sa.String(256), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_barber_blocks_id", "barber_blocks", ["id"])
    op.create_index("ix_barber_blocks_barber_id", "barber_blocks", ["barber_id"])
    op.create_index("ix_barber_blocks_business_id", "barber_blocks", ["business_id"])


def downgrade() -> None:
    op.drop_index("ix_barber_blocks_business_id", "barber_blocks")
    op.drop_index("ix_barber_blocks_barber_id", "barber_blocks")
    op.drop_index("ix_barber_blocks_id", "barber_blocks")
    op.drop_table("barber_blocks")
