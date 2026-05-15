"""add_interrupted_to_run_status

Revision ID: bd00c77384b2
Revises: 0007
Create Date: 2026-05-15 02:52:42.370818

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'bd00c77384b2'
down_revision: Union[str, None] = '0007'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # PostgreSQL requires ALTER TYPE ... ADD VALUE to be executed outside a transaction block
    with op.get_context().autocommit_block():
        op.execute("ALTER TYPE run_status_enum ADD VALUE IF NOT EXISTS 'interrupted'")

def downgrade() -> None:
    # PostgreSQL does not support removing values from an enum type easily.
    pass
