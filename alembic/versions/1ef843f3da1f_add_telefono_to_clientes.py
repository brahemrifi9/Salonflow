"""add telefono to clientes

Revision ID: 1ef843f3da1f
Revises: 95027982db73
Create Date: 2026-03-02 08:31:01.264827

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1ef843f3da1f'
down_revision: Union[str, None] = '95027982db73'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # 1️⃣ Add telefono column as nullable first
    op.add_column(
        "clientes",
        sa.Column("telefono", sa.String(length=32), nullable=True),
    )

    # 2️⃣ Backfill existing rows (so NOT NULL won't fail)
    op.execute(
        "UPDATE clientes SET telefono = 'UNKNOWN_' || id WHERE telefono IS NULL"
    )

    # 3️ Make telefono NOT NULL
    op.alter_column("clientes", "telefono", nullable=False)

    # 4️ Add unique constraint
    op.create_unique_constraint(
        "uq_clientes_telefono",
        "clientes",
        ["telefono"],
    )

    # 5️ Add index (optional but recommended)
    op.create_index(
        "ix_clientes_telefono",
        "clientes",
        ["telefono"],
    )

    # 6️ Make email nullable (if currently NOT NULL)
    op.alter_column("clientes", "email", nullable=True)


def downgrade():
    op.drop_index("ix_clientes_telefono", table_name="clientes")
    op.drop_constraint("uq_clientes_telefono", "clientes", type_="unique")
    op.drop_column("clientes", "telefono")
