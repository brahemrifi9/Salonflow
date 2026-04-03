"""add nullable business_id to all tenant tables

Revision ID: a002_add_business_id_nullable
Revises: a001_create_businesses
Create Date: 2026-03-28 00:00:02

SAFE: all columns added as NULLABLE first.
Unique constraints replaced with composite ones.
Existing data is unaffected (business_id will be NULL until migration 3).
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "a002_add_business_id_nullable"
down_revision: Union[str, None] = "a001_create_businesses"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # --- users ---
    op.add_column(
        "users",
        sa.Column("business_id", sa.Integer(), nullable=True),
    )
    op.create_foreign_key(
        "fk_users_business_id",
        "users", "businesses",
        ["business_id"], ["id"],
    )

    # --- barbers ---
    op.add_column(
        "barbers",
        sa.Column("business_id", sa.Integer(), nullable=True),
    )
    op.create_foreign_key(
        "fk_barbers_business_id",
        "barbers", "businesses",
        ["business_id"], ["id"],
    )

    # --- services ---
    # Drop old global unique on name, replace with composite
    op.drop_constraint("services_name_key", "services", type_="unique")
    op.add_column(
        "services",
        sa.Column("business_id", sa.Integer(), nullable=True),
    )
    op.create_foreign_key(
        "fk_services_business_id",
        "services", "businesses",
        ["business_id"], ["id"],
    )
    op.create_unique_constraint(
        "uq_services_business_name",
        "services",
        ["business_id", "name"],
    )

    # --- clientes ---
    # Drop old global unique on telefono, replace with composite
    op.drop_index("ix_clientes_telefono", table_name="clientes")
    op.add_column(
        "clientes",
        sa.Column("business_id", sa.Integer(), nullable=True),
    )
    op.create_foreign_key(
        "fk_clientes_business_id",
        "clientes", "businesses",
        ["business_id"], ["id"],
    )
    # New composite unique: one phone per business
    op.create_unique_constraint(
        "uq_clientes_business_telefono",
        "clientes",
        ["business_id", "telefono"],
    )
    # Recreate the index as non-unique (still useful for lookups)
    op.create_index("ix_clientes_telefono", "clientes", ["telefono"], unique=False)

    # --- bookings ---
    op.add_column(
        "bookings",
        sa.Column("business_id", sa.Integer(), nullable=True),
    )
    op.create_foreign_key(
        "fk_bookings_business_id",
        "bookings", "businesses",
        ["business_id"], ["id"],
    )

    # --- whatsapp_sessions ---
    # Drop old global unique on telefono, replace with composite
    op.drop_index("ix_whatsapp_sessions_telefono", table_name="whatsapp_sessions")
    op.add_column(
        "whatsapp_sessions",
        sa.Column("business_id", sa.Integer(), nullable=True),
    )
    op.create_foreign_key(
        "fk_whatsapp_sessions_business_id",
        "whatsapp_sessions", "businesses",
        ["business_id"], ["id"],
    )
    # New composite unique: one session per phone per business
    op.create_unique_constraint(
        "uq_whatsapp_sessions_business_telefono",
        "whatsapp_sessions",
        ["business_id", "telefono"],
    )
    # Recreate non-unique index
    op.create_index(
        "ix_whatsapp_sessions_telefono",
        "whatsapp_sessions",
        ["telefono"],
        unique=False,
    )


def downgrade() -> None:
    # whatsapp_sessions
    op.drop_constraint("uq_whatsapp_sessions_business_telefono", "whatsapp_sessions", type_="unique")
    op.drop_index("ix_whatsapp_sessions_telefono", table_name="whatsapp_sessions")
    op.create_index("ix_whatsapp_sessions_telefono", "whatsapp_sessions", ["telefono"], unique=True)
    op.drop_constraint("fk_whatsapp_sessions_business_id", "whatsapp_sessions", type_="foreignkey")
    op.drop_column("whatsapp_sessions", "business_id")

    # bookings
    op.drop_constraint("fk_bookings_business_id", "bookings", type_="foreignkey")
    op.drop_column("bookings", "business_id")

    # clientes
    op.drop_constraint("uq_clientes_business_telefono", "clientes", type_="unique")
    op.drop_index("ix_clientes_telefono", table_name="clientes")
    op.create_index("ix_clientes_telefono", "clientes", ["telefono"], unique=True)
    op.drop_constraint("fk_clientes_business_id", "clientes", type_="foreignkey")
    op.drop_column("clientes", "business_id")

    # services
    op.drop_constraint("uq_services_business_name", "services", type_="unique")
    op.drop_constraint("fk_services_business_id", "services", type_="foreignkey")
    op.drop_column("services", "business_id")
    op.create_unique_constraint("services_name_key", "services", ["name"])

    # barbers
    op.drop_constraint("fk_barbers_business_id", "barbers", type_="foreignkey")
    op.drop_column("barbers", "business_id")

    # users
    op.drop_constraint("fk_users_business_id", "users", type_="foreignkey")
    op.drop_column("users", "business_id")
