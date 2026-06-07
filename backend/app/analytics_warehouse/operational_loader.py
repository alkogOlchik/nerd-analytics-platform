"""Загрузка операционной БД без привязки к колонкам миграции 006."""

from __future__ import annotations

import uuid as uuid_module
from types import SimpleNamespace
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

# Минимальный набор колонок для ETL (достаточно схемы до 006)
_CLIENT_COLS = (
    "id",
    "username",
    "email",
    "full_name",
    "age",
    "gender",
    "city",
    "created_at",
)
_EMPLOYEE_COLS = (
    "id",
    "username",
    "full_name",
    "birthday",
    "phone",
    "sec_level",
    "status",
    "created_at",
)
_TICKET_COLS = (
    "id",
    "client_id",
    "responsible_id",
    "product",
    "status",
    "priority",
    "user_priority",
    "admin_priority",
    "date",
    "deadline",
    "closed_at",
    "reopened_count",
    "last_reopened_at",
    "ai_suggested_category",
    "final_category",
    "is_admin_changed",
    "keywords",
    "confidence",
    "sla_ttfr_min",
    "sla_ttr_min",
)
_REVIEW_COLS = (
    "id",
    "client_id",
    "ticket_id",
    "product",
    "rating",
    "comment",
    "sentiment",
    "ai_suggested_category",
    "final_category",
    "keywords_positive",
    "keywords_negative",
    "created_at",
)
_CHAT_COLS = (
    "id",
    "chat_id",
    "ticket_id",
    "client_id",
    "role",
    "product",
    "category",
    "resolved_by_ai",
    "message",
    "created_at",
)


async def _existing_columns(session: AsyncSession, table: str) -> set[str]:
    result = await session.execute(
        text(
            """
            SELECT column_name
            FROM information_schema.columns
            WHERE table_schema = 'public' AND table_name = :table
            """
        ),
        {"table": table},
    )
    return {row[0] for row in result.fetchall()}


async def _load_table(
    session: AsyncSession,
    table: str,
    wanted: tuple[str, ...],
) -> list[SimpleNamespace]:
    existing = await _existing_columns(session, table)
    cols = [c for c in wanted if c in existing]
    if not cols:
        return []
    quoted = ", ".join(f'"{c}"' for c in cols)
    result = await session.execute(text(f'SELECT {quoted} FROM "{table}"'))
    rows = []
    for row in result.fetchall():
        rows.append(SimpleNamespace(**dict(zip(cols, row))))
    return rows


async def load_operational(session: AsyncSession) -> tuple[
    list[SimpleNamespace],
    list[SimpleNamespace],
    list[SimpleNamespace],
    list[SimpleNamespace],
    list[SimpleNamespace],
]:
    clients = await _load_table(session, "clients", _CLIENT_COLS)
    employees = await _load_table(session, "employees", _EMPLOYEE_COLS)
    tickets = await _load_table(session, "tickets", _TICKET_COLS)
    reviews = await _load_table(session, "reviews", _REVIEW_COLS)
    chats = await _load_table(session, "chat_history", _CHAT_COLS)
    return clients, employees, tickets, reviews, chats


def get_attr(obj: Any, name: str, default: Any = None) -> Any:
    if isinstance(obj, dict):
        return obj.get(name, default)
    return getattr(obj, name, default)


def as_uuid(value: Any):
    """UUID-объект для записи в витрину (тот же id, что в nerd_db)."""
    import uuid as uuid_module

    key = normalize_key(value)
    if not key:
        return None
    return uuid_module.UUID(key)


def normalize_key(value: Any) -> str | None:
    """Единый ключ для UUID (tickets.id, chat_id, ticket_id в FK)."""
    if value is None:
        return None
    if isinstance(value, float) and str(value) == "nan":
        return None
    if isinstance(value, uuid_module.UUID):
        return str(value).lower()
    s = str(value).strip().lower()
    if not s or s in ("nan", "none", ""):
        return None
    try:
        return str(uuid_module.UUID(s)).lower()
    except ValueError:
        return s
