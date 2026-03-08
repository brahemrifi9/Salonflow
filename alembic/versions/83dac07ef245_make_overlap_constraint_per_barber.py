"""make overlap constraint per barber

Revision ID: 83dac07ef245
Revises: 4115d89ad357
Create Date: 2026-02-28 06:41:43.189324

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '83dac07ef245'
down_revision: Union[str, None] = '4115d89ad357'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # Drop old global overlap constraint
    op.execute("ALTER TABLE bookings DROP CONSTRAINT IF EXISTS no_overlapping_bookings;")

    # Ensure btree_gist extension exists (needed for barber_id WITH =)
    op.execute("CREATE EXTENSION IF NOT EXISTS btree_gist;")

    # Add new overlap constraint per barber
    op.execute("""
        ALTER TABLE bookings
        ADD CONSTRAINT no_overlapping_bookings
        EXCLUDE USING gist (
            barber_id WITH =,
            tsrange(start_time, end_time, '[)') WITH &&
        )
        WHERE (cancelled_at IS NULL);
    """)


def downgrade():
    # Drop per-barber overlap constraint
    op.execute("ALTER TABLE bookings DROP CONSTRAINT IF EXISTS no_overlapping_bookings;")

    # Recreate old global overlap constraint
    op.execute("""
        ALTER TABLE bookings
        ADD CONSTRAINT no_overlapping_bookings
        EXCLUDE USING gist (
            tsrange(start_time, end_time, '[)') WITH &&
        )
        WHERE (cancelled_at IS NULL);
    """)
