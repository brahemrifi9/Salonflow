"""add booking_ref

Revision ID: 5f34dc5a8adf
Revises: 1ef843f3da1f
Create Date: 2026-03-06 11:22:39.026831

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "5f34dc5a8adf"
down_revision: Union[str, None] = "1ef843f3da1f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "bookings",
        sa.Column("booking_ref", sa.String(length=12), nullable=True),
    )
    op.create_index(
        "ix_bookings_booking_ref",
        "bookings",
        ["booking_ref"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("ix_bookings_booking_ref", table_name="bookings")
    op.drop_column("bookings", "booking_ref")