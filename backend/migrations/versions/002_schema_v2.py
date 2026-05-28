"""schema v2 — AI fields on tickets/reviews, drop separate classification tables

Revision ID: 002
Revises: 001
Create Date: 2026-05-19
"""

from typing import Sequence, Union

from alembic import op

from backend.app.models.base import Base

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    # Для dev: пересоздаём схему целиком под новую модель
    Base.metadata.drop_all(bind)
    Base.metadata.create_all(bind)


def downgrade() -> None:
    bind = op.get_bind()
    Base.metadata.drop_all(bind)
