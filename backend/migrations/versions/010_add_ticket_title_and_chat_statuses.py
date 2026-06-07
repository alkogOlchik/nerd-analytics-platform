"""Add ticket title and new operator chat statuses

Revision ID: 010
Revises: 009
Create Date: 2026-06-07
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "010"
down_revision: Union[str, None] = "009"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TABLE tickets ADD COLUMN IF NOT EXISTS title VARCHAR(255)")
    op.alter_column("tickets", "product", existing_type=sa.String(64), nullable=True)


def downgrade() -> None:
    op.alter_column("tickets", "product", existing_type=sa.String(64), nullable=False)
    op.execute("ALTER TABLE tickets DROP COLUMN IF EXISTS title")
