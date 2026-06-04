"""Ticket workflow, roles, guest tickets, status history

Revision ID: 006
Revises: 005
Create Date: 2026-05-19
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "006"
down_revision: Union[str, None] = "005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_STATUS_MAP = {
    "open": "принято",
    "in_progress": "в_работе",
    "closed": "закрыто",
    "reopened": "принято",
}


def _column_exists(conn, table: str, column: str) -> bool:
    result = conn.execute(
        sa.text(
            "SELECT 1 FROM information_schema.columns "
            "WHERE table_name = :t AND column_name = :c"
        ),
        {"t": table, "c": column},
    )
    return result.fetchone() is not None


def _table_exists(conn, table: str) -> bool:
    result = conn.execute(
        sa.text(
            "SELECT 1 FROM information_schema.tables WHERE table_name = :t"
        ),
        {"t": table},
    )
    return result.fetchone() is not None


def _constraint_exists(conn, constraint: str) -> bool:
    result = conn.execute(
        sa.text(
            "SELECT 1 FROM information_schema.table_constraints "
            "WHERE constraint_name = :c"
        ),
        {"c": constraint},
    )
    return result.fetchone() is not None


def upgrade() -> None:
    conn = op.get_bind()

    for col, kwargs in [
        ("user_priority", {"type_": sa.String(), "nullable": True}),
        ("admin_priority", {"type_": sa.String(), "nullable": True}),
        ("guest_email", {"type_": sa.String(), "nullable": True}),
        ("guest_token", {"type_": sa.String(), "nullable": True}),
        ("status_updated_at", {"type_": sa.DateTime(timezone=True), "nullable": True}),
    ]:
        if not _column_exists(conn, "tickets", col):
            op.add_column("tickets", sa.Column(col, **kwargs))

    if not _constraint_exists(conn, "uq_tickets_guest_token"):
        op.create_unique_constraint("uq_tickets_guest_token", "tickets", ["guest_token"])

    if not _column_exists(conn, "employees", "role"):
        op.add_column(
            "employees",
            sa.Column("role", sa.String(), nullable=False, server_default="operator"),
        )

    for col, kwargs in [
        ("deletion_requested_at", {"type_": sa.DateTime(timezone=True), "nullable": True}),
        ("notify_email", {"type_": sa.Boolean(), "nullable": False, "server_default": sa.text("true")}),
        ("notify_push", {"type_": sa.Boolean(), "nullable": False, "server_default": sa.text("false")}),
    ]:
        if not _column_exists(conn, "clients", col):
            op.add_column("clients", sa.Column(col, **kwargs))

    if not _table_exists(conn, "ticket_status_history"):
        op.create_table(
            "ticket_status_history",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
            sa.Column("ticket_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tickets.id"), nullable=True),
            sa.Column("status_from", sa.String(), nullable=True),
            sa.Column("status_to", sa.String(), nullable=True),
            sa.Column("changed_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("employees.id"), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        )

    if not _table_exists(conn, "internal_comments"):
        op.create_table(
            "internal_comments",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
            sa.Column("ticket_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tickets.id"), nullable=True),
            sa.Column("employee_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("employees.id"), nullable=True),
            sa.Column("message", sa.Text(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        )

    for old_status, new_status in _STATUS_MAP.items():
        conn.execute(
            sa.text("UPDATE tickets SET status = :new WHERE status = :old"),
            {"new": new_status, "old": old_status},
        )

    op.alter_column("tickets", "status", server_default="принято")


def downgrade() -> None:
    op.alter_column("tickets", "status", server_default="open")

    _REVERSE = {v: k for k, v in _STATUS_MAP.items()}
    conn = op.get_bind()
    for new_status, old_status in _REVERSE.items():
        conn.execute(
            sa.text("UPDATE tickets SET status = :old WHERE status = :new"),
            {"old": old_status, "new": new_status},
        )

    op.drop_table("internal_comments")
    op.drop_table("ticket_status_history")

    op.drop_column("clients", "notify_push")
    op.drop_column("clients", "notify_email")
    op.drop_column("clients", "deletion_requested_at")
    op.drop_column("employees", "role")

    op.drop_constraint("uq_tickets_guest_token", "tickets", type_="unique")
    op.drop_column("tickets", "status_updated_at")
    op.drop_column("tickets", "guest_token")
    op.drop_column("tickets", "guest_email")
    op.drop_column("tickets", "admin_priority")
    op.drop_column("tickets", "user_priority")
