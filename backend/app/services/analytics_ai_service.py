"""AI-ассистент для дашборда аналитики: tool calling через Anthropic Claude API."""

from __future__ import annotations

import json
import logging
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.config import get_settings
from backend.app.schemas.analytics_ai import AnalyticsChatRequest, AnalyticsChatResponse, UiCommand

logger = logging.getLogger(__name__)
settings = get_settings()

_MODEL = "claude-sonnet-4-6"
_MAX_TOOL_ROUNDS = 5

_SYSTEM_PROMPT = (
    "Ты — аналитический ИИ-ассистент системы поддержки. "
    "Отвечай на русском языке. "
    "Используй инструменты для получения данных и управления дашбордом. "
    "Если нужны данные — вызови query_metric или detect_anomalies. "
    "Если нужно изменить вид дашборда — используй UI-инструменты (apply_filter, set_date_range и т.д.). "
    "Будь конкретным: называй числа, даты, категории из реальных данных."
)

ANALYTICS_TOOLS: list[dict] = [
    {
        "name": "apply_filter",
        "description": "Применить фильтр к дашборду. Frontend применяет его сразу.",
        "input_schema": {
            "type": "object",
            "properties": {
                "field": {"type": "string", "description": "Имя поля фильтра (product, status, priority и т.д.)"},
                "value": {"description": "Значение фильтра"},
            },
            "required": ["field", "value"],
        },
    },
    {
        "name": "set_date_range",
        "description": "Установить временной диапазон на дашборде.",
        "input_schema": {
            "type": "object",
            "properties": {
                "date_from": {"type": "string", "description": "ISO date, например 2026-05-01"},
                "date_to": {"type": "string", "description": "ISO date, например 2026-06-07"},
            },
            "required": ["date_from", "date_to"],
        },
    },
    {
        "name": "highlight_element",
        "description": "Визуально выделить точку на график��.",
        "input_schema": {
            "type": "object",
            "properties": {
                "chart_id": {"type": "string"},
                "point_id": {"type": "string"},
            },
            "required": ["chart_id", "point_id"],
        },
    },
    {
        "name": "change_chart_type",
        "description": "Изменить тип графика.",
        "input_schema": {
            "type": "object",
            "properties": {
                "chart_id": {"type": "string"},
                "type": {"type": "string", "enum": ["line", "bar", "pie", "area", "scatter"]},
            },
            "required": ["chart_id", "type"],
        },
    },
    {
        "name": "query_metric",
        "description": "Запросить метрику из аналитической БД.",
        "input_schema": {
            "type": "object",
            "properties": {
                "metric": {
                    "type": "string",
                    "enum": [
                        "tickets_total",
                        "tickets_open",
                        "avg_ticket_lifetime_hours",
                        "reopen_rate",
                        "avg_rating",
                        "ai_resolution_rate",
                        "avg_ttfr_minutes",
                        "avg_ttr_minutes",
                    ],
                },
                "filters": {
                    "type": "object",
                    "description": "Опциональные фильтры: product, date_from, date_to, priority",
                    "properties": {
                        "product": {"type": "string"},
                        "date_from": {"type": "string"},
                        "date_to": {"type": "string"},
                        "priority": {"type": "string"},
                    },
                },
            },
            "required": ["metric"],
        },
    },
    {
        "name": "detect_anomalies",
        "description": "Обнаружить аномалии в обращениях за последние N дней (rolling_avg + 2σ).",
        "input_schema": {
            "type": "object",
            "properties": {
                "days": {"type": "integer", "description": "Количество дней для анализа", "default": 7},
            },
            "required": ["days"],
        },
    },
    {
        "name": "create_ticket",
        "description": "Создать тикет от имени текущего администратора.",
        "input_schema": {
            "type": "object",
            "properties": {
                "product_id": {"type": "string", "description": "UUID продукта"},
                "description": {"type": "string"},
                "priority": {"type": "string", "enum": ["low", "medium", "high"]},
            },
            "required": ["product_id", "description", "priority"],
        },
    },
]

_UI_TOOL_NAMES = {"apply_filter", "set_date_range", "highlight_element", "change_chart_type"}


async def _execute_tool(
    tool_name: str,
    tool_input: dict[str, Any],
    db: AsyncSession,
    current_user_id: uuid.UUID,
    ui_commands: list[UiCommand],
    created_ticket_id_ref: list[uuid.UUID | None],
) -> str:
    if tool_name in _UI_TOOL_NAMES:
        cmd = UiCommand(type=tool_name, **{k: v for k, v in tool_input.items() if k in UiCommand.model_fields})
        ui_commands.append(cmd)
        return json.dumps({"status": "ui_command_queued"})

    if tool_name == "query_metric":
        return await _query_metric(db, tool_input)

    if tool_name == "detect_anomalies":
        return await _detect_anomalies(db, tool_input.get("days", 7))

    if tool_name == "create_ticket":
        ticket_id = await _create_ticket(db, current_user_id, tool_input)
        created_ticket_id_ref[0] = ticket_id
        return json.dumps({"ticket_id": str(ticket_id)})

    return json.dumps({"error": f"Unknown tool: {tool_name}"})


async def _query_metric(db: AsyncSession, tool_input: dict[str, Any]) -> str:
    from sqlalchemy import func, select

    from backend.app.models.enums import TicketStatus
    from backend.app.models.review import Review
    from backend.app.models.ticket import Ticket

    metric = tool_input.get("metric", "")
    filters = tool_input.get("filters", {}) or {}

    date_from = _parse_date(filters.get("date_from")) or (datetime.now(UTC) - timedelta(days=30))
    date_to = _parse_date(filters.get("date_to")) or datetime.now(UTC)

    try:
        if metric == "tickets_total":
            stmt = select(func.count(Ticket.id)).where(Ticket.date >= date_from, Ticket.date <= date_to)
            result = await db.scalar(stmt)
            return json.dumps({"metric": metric, "value": result or 0})

        if metric == "tickets_open":
            open_statuses = [s.value for s in TicketStatus if s != TicketStatus.closed and s != TicketStatus.rejected]
            stmt = select(func.count(Ticket.id)).where(Ticket.status.in_(open_statuses))
            result = await db.scalar(stmt)
            return json.dumps({"metric": metric, "value": result or 0})

        if metric == "avg_ticket_lifetime_hours":
            stmt = select(func.avg(
                func.extract("epoch", Ticket.closed_at - Ticket.date) / 3600
            )).where(
                Ticket.closed_at.isnot(None),
                Ticket.date >= date_from,
                Ticket.date <= date_to,
            )
            result = await db.scalar(stmt)
            return json.dumps({"metric": metric, "value": round(float(result or 0), 1)})

        if metric == "reopen_rate":
            total = await db.scalar(select(func.count(Ticket.id)).where(Ticket.date >= date_from, Ticket.date <= date_to))
            reopened = await db.scalar(select(func.count(Ticket.id)).where(
                Ticket.reopened_count > 0, Ticket.date >= date_from, Ticket.date <= date_to
            ))
            rate = round((reopened or 0) / (total or 1) * 100, 1)
            return json.dumps({"metric": metric, "value": rate, "unit": "%"})

        if metric == "avg_rating":
            stmt = select(func.avg(Review.rating)).where(
                Review.created_at >= date_from, Review.created_at <= date_to
            )
            result = await db.scalar(stmt)
            return json.dumps({"metric": metric, "value": round(float(result or 0), 2)})

        if metric == "ai_resolution_rate":
            from backend.app.models.chat import ChatHistory
            from backend.app.models.enums import ChatRole

            total = await db.scalar(select(func.count(Ticket.id)).where(Ticket.date >= date_from, Ticket.date <= date_to))
            escalated = await db.scalar(select(func.count(Ticket.id)).where(
                Ticket.date >= date_from,
                Ticket.date <= date_to,
                Ticket.status != TicketStatus.accepted.value,
                Ticket.responsible_id.isnot(None),
            ))
            ai_resolved = (total or 0) - (escalated or 0)
            rate = round(ai_resolved / (total or 1) * 100, 1)
            return json.dumps({"metric": metric, "value": rate, "unit": "%", "ai_resolved": ai_resolved, "total": total})

        return json.dumps({"error": f"Unknown metric: {metric}"})

    except Exception as exc:
        logger.exception("query_metric error: %s", exc)
        return json.dumps({"error": str(exc)})


async def _detect_anomalies(db: AsyncSession, days: int) -> str:
    import statistics

    from sqlalchemy import func, select

    from backend.app.models.ticket import Ticket

    now = datetime.now(UTC)
    window_start = now - timedelta(days=days)
    baseline_start = now - timedelta(days=days * 4)

    try:
        # Count per day over baseline
        stmt = select(
            func.date_trunc("day", Ticket.date).label("day"),
            func.count(Ticket.id).label("cnt"),
        ).where(Ticket.date >= baseline_start, Ticket.date <= now).group_by("day")
        rows = (await db.execute(stmt)).all()
        counts = [int(r.cnt) for r in rows]

        if len(counts) < 4:
            return json.dumps({"anomalies": [], "note": "Not enough data"})

        avg = statistics.mean(counts)
        stdev = statistics.stdev(counts) if len(counts) > 1 else 0
        threshold = avg + 2 * stdev

        recent_stmt = select(
            func.date_trunc("day", Ticket.date).label("day"),
            func.count(Ticket.id).label("cnt"),
        ).where(Ticket.date >= window_start, Ticket.date <= now).group_by("day")
        recent_rows = (await db.execute(recent_stmt)).all()

        anomalies = [
            {"date": str(r.day)[:10], "count": int(r.cnt), "threshold": round(threshold, 1)}
            for r in recent_rows
            if int(r.cnt) > threshold
        ]
        return json.dumps({"anomalies": anomalies, "rolling_avg": round(avg, 1), "threshold": round(threshold, 1)})

    except Exception as exc:
        logger.exception("detect_anomalies error: %s", exc)
        return json.dumps({"error": str(exc)})


async def _create_ticket(
    db: AsyncSession,
    current_user_id: uuid.UUID,
    tool_input: dict[str, Any],
) -> uuid.UUID:
    from backend.app.models.ticket import Ticket

    now = datetime.now(UTC)
    product_id_str = tool_input.get("product_id")

    ticket = Ticket(
        client_id=current_user_id,
        product_id=uuid.UUID(product_id_str) if product_id_str else None,
        title=tool_input.get("description", "")[:120],
        status="принято",
        priority=tool_input.get("priority", "medium"),
        admin_priority=tool_input.get("priority", "medium"),
        date=now,
        deadline=now + timedelta(hours=24),
        ai_suggested_category="analytics_ai",
        final_category="analytics_ai",
    )
    db.add(ticket)
    await db.commit()
    await db.refresh(ticket)
    return ticket.id


def _parse_date(val: str | None) -> datetime | None:
    if not val:
        return None
    try:
        return datetime.fromisoformat(val).replace(tzinfo=UTC)
    except ValueError:
        return None


async def analytics_chat(
    db: AsyncSession,
    current_user_id: uuid.UUID,
    data: AnalyticsChatRequest,
) -> AnalyticsChatResponse:
    if not settings.ANTHROPIC_API_KEY:
        return AnalyticsChatResponse(
            reply="Anthropic API key не настроен. Укажите ANTHROPIC_API_KEY в .env.",
        )

    try:
        import anthropic
    except ImportError:
        return AnalyticsChatResponse(
            reply="Пакет anthropic не установлен. Выполните: pip install anthropic",
        )

    client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)

    context_note = (
        f"Активный дашборд: {data.dashboard_context.active_dashboard}. "
        f"Текущие фильтры: {json.dumps(data.dashboard_context.current_filters, ensure_ascii=False)}. "
        f"Период: {data.dashboard_context.date_range.from_} — {data.dashboard_context.date_range.to}."
    )

    messages: list[dict] = [
        {"role": "user", "content": f"{context_note}\n\n{data.message}"},
    ]

    ui_commands: list[UiCommand] = []
    created_ticket_id_ref: list[uuid.UUID | None] = [None]

    for _ in range(_MAX_TOOL_ROUNDS):
        response = await client.messages.create(
            model=_MODEL,
            max_tokens=1024,
            system=_SYSTEM_PROMPT,
            tools=ANALYTICS_TOOLS,  # type: ignore[arg-type]
            messages=messages,  # type: ignore[arg-type]
        )

        # Collect assistant content block list
        assistant_content = response.content
        messages.append({"role": "assistant", "content": assistant_content})

        if response.stop_reason == "end_turn":
            text_blocks = [b.text for b in assistant_content if hasattr(b, "text")]
            reply = " ".join(text_blocks).strip() or "Готово."
            break

        if response.stop_reason == "tool_use":
            tool_results = []
            for block in assistant_content:
                if block.type != "tool_use":
                    continue
                result_text = await _execute_tool(
                    block.name,
                    block.input,
                    db,
                    current_user_id,
                    ui_commands,
                    created_ticket_id_ref,
                )
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": result_text,
                })
            messages.append({"role": "user", "content": tool_results})
            continue

        # Unexpected stop reason
        text_blocks = [b.text for b in assistant_content if hasattr(b, "text")]
        reply = " ".join(text_blocks).strip() or "Завершено."
        break
    else:
        reply = "Превышено максимальное количество итераций инструментов."

    return AnalyticsChatResponse(
        reply=reply,
        ui_commands=ui_commands,
        created_ticket_id=created_ticket_id_ref[0],
    )
