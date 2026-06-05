"""Notification read state and display fields

Revision ID: 008
Revises: 007
Create Date: 2026-05-19
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "008"
down_revision: Union[str, None] = "007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "notifications",
        sa.Column("is_read", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )
    op.add_column(
        "notifications",
        sa.Column("event_type", sa.String(length=32), nullable=False, server_default="ticket_update"),
    )
    op.add_column("notifications", sa.Column("title", sa.String(length=255), nullable=True))
    op.add_column("notifications", sa.Column("message", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("notifications", "message")
    op.drop_column("notifications", "title")
    op.drop_column("notifications", "event_type")
    op.drop_column("notifications", "is_read")
