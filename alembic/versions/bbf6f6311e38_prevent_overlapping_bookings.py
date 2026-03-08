"""prevent overlapping bookings

Revision ID: bbf6f6311e38
Revises: 8e8a941b9647
Create Date: 2026-02-25 17:38:09.027823

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'bbf6f6311e38'   
down_revision = '8e8a941b9647'
branch_labels = None
depends_on = None


def upgrade():
    # Ensure extension exists (needed for barber_id WITH = in GiST)
    op.execute("CREATE EXTENSION IF NOT EXISTS btree_gist;")

    # Drop old constraint if it exists (name may differ in your DB)
    op.execute("ALTER TABLE bookings DROP CONSTRAINT IF EXISTS no_overlapping_bookings;")

    # Create new per-barber constraint
    op.execute("""
        ALTER TABLE bookings
        ADD CONSTRAINT no_overlapping_bookings
        EXCLUDE USING gist (
            barber_id WITH =,
            tstzrange(start_time, end_time, '[)') WITH &&
        )
        WHERE (cancelled_at IS NULL);
    """)



def downgrade():
    # Drop the per-barber constraint
    op.execute("ALTER TABLE bookings DROP CONSTRAINT IF EXISTS no_overlapping_bookings;")

    # Recreate the old global constraint (fallback)
    op.execute("""
        ALTER TABLE bookings
        ADD CONSTRAINT no_overlapping_bookings
        EXCLUDE USING gist (
            tstzrange(start_time, end_time, '[)') WITH &&
        )
        WHERE (cancelled_at IS NULL);
    """)
