"""chat_files table

Revision ID: 007
Revises: 006
Create Date: 2026-06-04
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "007"
down_revision: Union[str, None] = "006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _table_exists(conn, table: str) -> bool:
    result = conn.execute(
        sa.text("SELECT 1 FROM information_schema.tables WHERE table_name = :t"),
        {"t": table},
    )
    return result.fetchone() is not None


def upgrade() -> None:
    conn = op.get_bind()
    if not _table_exists(conn, "chat_files"):
        op.create_table(
            "chat_files",
            sa.Column(
                "id",
                postgresql.UUID(as_uuid=True),
                primary_key=True,
                server_default=sa.text("gen_random_uuid()"),
            ),
            sa.Column(
                "client_id",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("clients.id"),
                nullable=False,
            ),
            sa.Column("chat_id", postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column("s3_key", sa.Text(), nullable=False),
            sa.Column("filename", sa.Text(), nullable=False),
            sa.Column("content_type", sa.Text(), nullable=False),
            sa.Column("size_bytes", sa.Integer(), nullable=False),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("now()"),
                nullable=False,
            ),
        )
        op.create_index("ix_chat_files_client_id", "chat_files", ["client_id"])
        op.create_index("ix_chat_files_chat_id", "chat_files", ["chat_id"])


def downgrade() -> None:
    op.drop_index("ix_chat_files_chat_id", table_name="chat_files")
    op.drop_index("ix_chat_files_client_id", table_name="chat_files")
    op.drop_table("chat_files")
