"""timezone aware booking datetimes

Revision ID: 95027982db73
Revises: 83dac07ef245
Create Date: 2026-02-28 08:51:41.344138

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '95027982db73'
down_revision: Union[str, None] = '83dac07ef245'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # 1) Drop the old exclusion constraint (it uses tsrange)
    op.execute("ALTER TABLE bookings DROP CONSTRAINT IF EXISTS no_overlapping_bookings")

    # 2) Make BOTH columns timestamptz (timezone aware)
    op.alter_column(
        "bookings",
        "start_time",
        type_=sa.DateTime(timezone=True),
        postgresql_using="start_time AT TIME ZONE 'UTC'",
    )
    op.alter_column(
        "bookings",
        "end_time",
        type_=sa.DateTime(timezone=True),
        postgresql_using="end_time AT TIME ZONE 'UTC'",
    )

    # optional but recommended if you store it:
    # op.alter_column(
    #     "bookings",
    #     "cancelled_at",
    #     type_=sa.DateTime(timezone=True),
    #     postgresql_using="cancelled_at AT TIME ZONE 'UTC'",
    # )

    # 3) Recreate exclusion constraint using tstzrange (for timestamptz)
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
    op.execute("ALTER TABLE bookings DROP CONSTRAINT IF EXISTS no_overlapping_bookings")
    
    op.alter_column(
        "bookings",
        "start_time",
        type_=sa.DateTime(timezone=False),
        postgresql_using="start_time::timestamp",
    )
    op.alter_column(
        "bookings",
        "end_time",
        type_=sa.DateTime(timezone=False),
        postgresql_using="end_time::timestamp",
    )

    op.execute("""
        ALTER TABLE bookings
        ADD CONSTRAINT no_overlapping_bookings
        EXCLUDE USING gist (
            barber_id WITH =,
            tsrange(start_time, end_time, '[)') WITH &&
        )
        WHERE (cancelled_at IS NULL);
    """)
