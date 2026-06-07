"""schema v3 — SLA fields, chat_id, reviews.product, drop ticket.type/sentiment

Revision ID: 003
Revises: 002
Create Date: 2026-05-19
"""

from typing import Sequence, Union

from alembic import op

from backend.app.models.base import Base

revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    Base.metadata.drop_all(bind)
    Base.metadata.create_all(bind)


def downgrade() -> None:
    bind = op.get_bind()
    Base.metadata.drop_all(bind)
