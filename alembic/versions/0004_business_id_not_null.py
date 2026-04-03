"""set business_id not null on all tenant tables

Revision ID: a004_business_id_not_null
Revises: a003_backfill_spain_business
Create Date: 2026-03-28 00:00:04

SAFE ONLY AFTER migration 3 has run successfully.
If any row still has business_id = NULL, this migration will fail —
which is the correct behavior. Fix the data before retrying.
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import text

revision: str = "a004_business_id_not_null"
down_revision: Union[str, None] = "a003_backfill_spain_business"
branch_labels = None
depends_on = None

TABLES = ["users", "barbers", "services", "clientes", "bookings", "whatsapp_sessions"]


def upgrade() -> None:
    conn = op.get_bind()

    # Safety check: ensure no NULLs remain before applying NOT NULL constraint
    for table in TABLES:
        result = conn.execute(
            text(f"SELECT COUNT(*) FROM {table} WHERE business_id IS NULL")
        )
        null_count = result.scalar()
        if null_count > 0:
            raise RuntimeError(
                f"Table '{table}' still has {null_count} rows with NULL business_id. "
                f"Run migration a003 backfill first and verify all rows are assigned."
            )

    # All clear — apply NOT NULL constraints
    for table in TABLES:
        op.alter_column(table, "business_id", nullable=False)


def downgrade() -> None:
    for table in TABLES:
        op.alter_column(table, "business_id", nullable=True)
