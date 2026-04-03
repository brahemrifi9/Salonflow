"""backfill spain business and assign all existing rows

Revision ID: a003_backfill_spain_business
Revises: a002_add_business_id_nullable
Create Date: 2026-03-28 00:00:03

CRITICAL: This migration creates the initial Spain business row and assigns
all existing production data to it. Must run before migration 4 (NOT NULL).

Safe: UPDATE with WHERE business_id IS NULL — idempotent if re-run.
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import text

revision: str = "a003_backfill_spain_business"
down_revision: Union[str, None] = "a002_add_business_id_nullable"
branch_labels = None
depends_on = None

# Change these values to match your real Spain business details
SPAIN_BUSINESS_NAME = "Peluqueria El Haddouchi"
SPAIN_WHATSAPP_PHONE_NUMBER_ID = ""  # <-- FILL THIS IN from your Meta dashboard


def upgrade() -> None:
    conn = op.get_bind()

    # 1. Insert the Spain business (id will be 1 if table is empty)
    conn.execute(
        text("""
            INSERT INTO businesses (name, country, language, currency, timezone, whatsapp_phone_number_id, is_active, created_at)
            VALUES (:name, 'ES', 'es', 'EUR', 'Europe/Madrid', :wa_phone_id, true, NOW())
            ON CONFLICT DO NOTHING
        """),
        {
            "name": SPAIN_BUSINESS_NAME,
            "wa_phone_id": SPAIN_WHATSAPP_PHONE_NUMBER_ID or None,
        }
    )

    # 2. Get the Spain business id (safe: works whether we just inserted or it existed)
    result = conn.execute(
        text("SELECT id FROM businesses WHERE country = 'ES' ORDER BY id ASC LIMIT 1")
    )
    row = result.fetchone()
    if row is None:
        raise RuntimeError("Failed to find or create Spain business row.")
    spain_id = row[0]

    # 3. Backfill all existing rows that have no business_id yet
    for table in ["users", "barbers", "services", "clientes", "bookings", "whatsapp_sessions"]:
        conn.execute(
            text(f"UPDATE {table} SET business_id = :bid WHERE business_id IS NULL"),
            {"bid": spain_id}
        )

    print(f"[migration] All existing rows assigned to business_id={spain_id} ({SPAIN_BUSINESS_NAME})")


def downgrade() -> None:
    conn = op.get_bind()

    # Null out the business_id on all rows
    for table in ["users", "barbers", "services", "clientes", "bookings", "whatsapp_sessions"]:
        conn.execute(text(f"UPDATE {table} SET business_id = NULL"))

    # Remove the Spain business row
    conn.execute(text("DELETE FROM businesses WHERE country = 'ES'"))
