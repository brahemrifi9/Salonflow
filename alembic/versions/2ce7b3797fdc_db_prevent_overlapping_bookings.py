"""db: prevent overlapping bookings

Revision ID: 2ce7b3797fdc
Revises: bc30e85ff03d
Create Date: 2026-02-25 16:21:26.166028

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2ce7b3797fdc'
down_revision: Union[str, None] = 'e7b72fb1dbb3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Prevent overlapping bookings for a single-barber MVP.
    # Only active bookings (cancelled_at IS NULL) participate.
    op.execute("""
         ALTER TABLE bookings
        ADD CONSTRAINT no_overlapping_bookings
        EXCLUDE USING gist (
            tsrange(
                start_time,
                start_time + (duration_minutes || ' minutes')::interval,
                '[)'
            ) WITH &&
        )
        WHERE (cancelled_at IS NULL);
    """)


def downgrade() -> None:
    op.execute("""
        ALTER TABLE bookings
        DROP CONSTRAINT IF EXISTS no_overlapping_bookings;
    """)
