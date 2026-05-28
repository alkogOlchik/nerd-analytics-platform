"""Сборка аналитической витрины из операционной БД nerd_db."""

from __future__ import annotations

import math
from collections import Counter, defaultdict
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.analytics_warehouse.models import (
    AdminEffective,
    AiEffective,
    FactForecast,
    FactProblems,
    FactReviews,
    FactUsers,
    General,
)
from backend.app.analytics_warehouse.operational_loader import get_attr, load_operational

CLOSED_STATUSES = {"закрыто", "closed"}

_WEEKDAYS_RU = [
    "Понедельник",
    "Вторник",
    "Среда",
    "Четверг",
    "Пятница",
    "Суббота",
    "Воскресенье",
]

_PRIORITY_RU = {"low": "Низкий", "medium": "Обычный", "high": "Срочный"}
_GENDER_RU = {"male": "М", "female": "Ж", "m": "М", "f": "Ж"}


def _to_date(dt: datetime | None) -> date | None:
    if dt is None:
        return None
    if dt.tzinfo:
        dt = dt.astimezone(UTC)
    return dt.date()


def _age_group(age: int | None) -> str | None:
    if age is None:
        return None
    if age < 18:
        return "<18"
    if age <= 25:
        return "18-25"
    if age <= 35:
        return "26-35"
    if age <= 45:
        return "36-45"
    if age <= 55:
        return "46-55"
    return "55+"


def _priority_label(ticket) -> str:
    raw = (
        get_attr(ticket, "admin_priority")
        or get_attr(ticket, "user_priority")
        or get_attr(ticket, "priority")
    )
    return _PRIORITY_RU.get(raw, raw or "Обычный")


def _is_closed(status: str | None) -> bool:
    return status in CLOSED_STATUSES


async def _clear_warehouse(adb: AsyncSession) -> None:
    for model in (
        FactForecast,
        FactProblems,
        FactReviews,
        FactUsers,
        AdminEffective,
        AiEffective,
        General,
    ):
        await adb.execute(delete(model))


async def build_warehouse(
    odb: AsyncSession,
    adb: AsyncSession,
    *,
    forecast_xlsx: Path | None = None,
) -> dict[str, int]:
    clients, employees, tickets, reviews, chats = await load_operational(odb)
    await _clear_warehouse(adb)

    client_map = {
        c.id: idx + 1
        for idx, c in enumerate(sorted(clients, key=lambda x: get_attr(x, "created_at")))
    }
    ticket_map = {
        t.id: idx + 1 for idx, t in enumerate(sorted(tickets, key=lambda x: get_attr(x, "date")))
    }
    employee_map = {e.id: get_attr(e, "full_name") or get_attr(e, "username") for e in employees}
    client_by_id = {c.id: c for c in clients}

    review_by_ticket: dict = {}
    for r in reviews:
        tid = get_attr(r, "ticket_id")
        if tid:
            review_by_ticket[tid] = r

    chats_by_ticket: dict = defaultdict(list)
    chats_by_chat: dict = defaultdict(list)
    for ch in chats:
        tid = get_attr(ch, "ticket_id")
        cid = get_attr(ch, "chat_id")
        if tid:
            chats_by_ticket[tid].append(ch)
        chats_by_chat[cid].append(ch)

    first_admin_at: dict = {}
    for tid, msgs in chats_by_ticket.items():
        admin_msgs = [m for m in msgs if get_attr(m, "role") == "admin"]
        if admin_msgs:
            first_admin_at[tid] = min(get_attr(m, "created_at") for m in admin_msgs)

    # ── D1: general ──
    for ticket in tickets:
        tid = ticket_map[ticket.id]
        client = client_by_id.get(ticket.client_id)
        rev = review_by_ticket.get(ticket.id)
        closed = get_attr(ticket, "closed_at")
        t_date = get_attr(ticket, "date")
        ttl = None
        if closed and t_date:
            ttl = (closed - t_date).total_seconds() / 3600
        adb.add(
            General(
                ticket_id=tid,
                created_at=_to_date(t_date),
                closed_at=_to_date(closed),
                product=get_attr(ticket, "product"),
                category=get_attr(ticket, "final_category") or get_attr(ticket, "ai_suggested_category"),
                status=get_attr(ticket, "status"),
                priority=_priority_label(ticket),
                admin=employee_map.get(get_attr(ticket, "responsible_id"))
                if get_attr(ticket, "responsible_id")
                else None,
                city=get_attr(client, "city") if client else None,
                age_group=_age_group(get_attr(client, "age")) if client else None,
                ttl_hours=round(ttl, 2) if ttl is not None else None,
                is_reopened=1 if (get_attr(ticket, "reopened_count") or 0) > 0 else 0,
                reopen_count=get_attr(ticket, "reopened_count") or 0,
                rating=get_attr(rev, "rating") if rev else None,
            )
        )

    # ── D2: ai_effective (one row per chat_id) ──
    dialog_id = 1
    for chat_id, msgs in sorted(chats_by_chat.items(), key=lambda x: str(x[0])):
        msgs = sorted(msgs, key=lambda m: get_attr(m, "created_at"))
        if not msgs:
            continue
        ticket_uuid = get_attr(msgs[0], "ticket_id")
        ticket_int = ticket_map.get(ticket_uuid) if ticket_uuid else None
        ticket_obj = next((t for t in tickets if t.id == ticket_uuid), None) if ticket_uuid else None
        resolved = any(get_attr(m, "resolved_by_ai") for m in msgs)
        escalated = 0 if resolved else 1
        resolution_ai = None
        if resolved and len(msgs) >= 2:
            resolution_ai = (
                get_attr(msgs[-1], "created_at") - get_attr(msgs[0], "created_at")
            ).total_seconds() / 60
        resolution_human = None
        if ticket_obj and get_attr(ticket_obj, "closed_at") and escalated:
            resolution_human = (
                get_attr(ticket_obj, "closed_at") - get_attr(msgs[-1], "created_at")
            ).total_seconds() / 60

        adb.add(
            AiEffective(
                dialog_id=dialog_id,
                ticket_id=ticket_int,
                date=_to_date(get_attr(msgs[0], "created_at")),
                product=get_attr(msgs[0], "product")
                or (get_attr(ticket_obj, "product") if ticket_obj else None),
                msg_count_before_escalation=len(msgs),
                is_resolved_by_ai=1 if resolved else 0,
                escalated_to_human=escalated,
                ai_response_sec=None,
                ai_category_suggested=get_attr(ticket_obj, "ai_suggested_category")
                if ticket_obj
                else get_attr(msgs[0], "category"),
                admin_changed_category=1
                if ticket_obj and get_attr(ticket_obj, "is_admin_changed")
                else 0,
                final_category=get_attr(ticket_obj, "final_category")
                if ticket_obj
                else get_attr(msgs[0], "category"),
                resolution_time_ai_min=round(resolution_ai, 2) if resolution_ai else None,
                resolution_time_human_min=round(resolution_human, 2) if resolution_human else None,
            )
        )
        dialog_id += 1

    # ── D3: admin_effective ──
    for ticket in tickets:
        tid = ticket_map[ticket.id]
        first_admin = first_admin_at.get(ticket.id)
        t_date = get_attr(ticket, "date")
        ttfr = None
        if first_admin and t_date:
            ttfr = (first_admin - t_date).total_seconds() / 60
        closed_at = get_attr(ticket, "closed_at")
        ttr = None
        if closed_at and t_date:
            ttr = (closed_at - t_date).total_seconds() / 60
        sla_ttfr = get_attr(ticket, "sla_ttfr_min")
        sla_ttr = get_attr(ticket, "sla_ttr_min")
        ttfr_met = (
            1
            if ttfr is not None and sla_ttfr is not None and ttfr <= sla_ttfr
            else 0 if ttfr is not None and sla_ttfr is not None
            else None
        )
        ttr_met = (
            1
            if ttr is not None and sla_ttr is not None and ttr <= sla_ttr
            else 0 if ttr is not None and sla_ttr is not None
            else None
        )
        rev = review_by_ticket.get(ticket.id)
        dt = t_date
        adb.add(
            AdminEffective(
                ticket_id=tid,
                date=_to_date(dt),
                hour=dt.hour if dt else None,
                day_of_week=_WEEKDAYS_RU[dt.weekday()] if dt else None,
                product=get_attr(ticket, "product"),
                category=get_attr(ticket, "final_category") or get_attr(ticket, "ai_suggested_category"),
                priority=_priority_label(ticket),
                admin=employee_map.get(get_attr(ticket, "responsible_id"))
                if get_attr(ticket, "responsible_id")
                else None,
                ttfr_min=round(ttfr, 2) if ttfr is not None else None,
                ttr_min=round(ttr, 2) if ttr is not None else None,
                sla_ttfr_min=sla_ttfr,
                sla_ttr_min=sla_ttr,
                ttfr_met=ttfr_met,
                ttr_met=ttr_met,
                tickets_closed=1 if _is_closed(get_attr(ticket, "status")) else 0,
                rating_from_user=get_attr(rev, "rating") if rev else None,
            )
        )

    # ── D4: fact_users ──
    tickets_by_client: dict = defaultdict(list)
    for t in tickets:
        tickets_by_client[t.client_id].append(t)

    for client in clients:
        uid = client_map[client.id]
        client_tickets = sorted(
            tickets_by_client.get(client.id, []), key=lambda t: get_attr(t, "date")
        )
        products = sorted({get_attr(t, "product") for t in client_tickets})
        open_cnt = sum(1 for t in client_tickets if not _is_closed(get_attr(t, "status")))
        closed_cnt = sum(1 for t in client_tickets if _is_closed(get_attr(t, "status")))
        first_d = _to_date(get_attr(client_tickets[0], "date")) if client_tickets else None
        last_d = _to_date(get_attr(client_tickets[-1], "date")) if client_tickets else None
        ret7 = ret14 = ret30 = 0
        if len(client_tickets) >= 2:
            first_dt = get_attr(client_tickets[0], "date")
            for t in client_tickets[1:]:
                delta = (get_attr(t, "date") - first_dt).days
                if delta <= 7:
                    ret7 = 1
                if delta <= 14:
                    ret14 = 1
                if delta <= 30:
                    ret30 = 1
        gender_raw = get_attr(client, "gender")
        adb.add(
            FactUsers(
                user_id=uid,
                registration_date=_to_date(get_attr(client, "created_at")),
                gender=_GENDER_RU.get(gender_raw or "", "Не указан") if gender_raw else "Не указан",
                age_group=_age_group(get_attr(client, "age")),
                city=get_attr(client, "city"),
                product=products or None,
                total_tickets=len(client_tickets),
                open_tickets=open_cnt,
                closed_tickets=closed_cnt,
                first_ticket_date=first_d,
                last_ticket_date=last_d,
                retention_7d=ret7,
                retention_14d=ret14,
                retention_30d=ret30,
            )
        )

    # ── D5: fact_reviews ──
    for idx, review in enumerate(sorted(reviews, key=lambda r: get_attr(r, "created_at")), start=1):
        client = client_by_id.get(review.client_id)
        rid = get_attr(review, "ticket_id")
        ticket = next((t for t in tickets if t.id == rid), None) if rid else None
        adb.add(
            FactReviews(
                review_id=idx,
                ticket_id=ticket_map.get(rid) if rid else None,
                date=_to_date(get_attr(review, "created_at")),
                product=get_attr(review, "product") or (get_attr(ticket, "product") if ticket else None),
                category=get_attr(review, "final_category") or get_attr(review, "ai_suggested_category"),
                city=get_attr(client, "city") if client else None,
                age_group=_age_group(get_attr(client, "age")) if client else None,
                rating=get_attr(review, "rating"),
                review_text=get_attr(review, "comment"),
                sentiment=get_attr(review, "sentiment"),
                keywords_positive=get_attr(review, "keywords_positive"),
                keywords_negative=get_attr(review, "keywords_negative"),
            )
        )

    # ── D6: fact_problems + anomalies ──
    now = datetime.now(UTC)
    counts_48h: Counter[tuple[str, str]] = Counter()
    history_counts: dict[tuple[str, str], list[int]] = defaultdict(list)

    for ticket in tickets:
        cat = (
            get_attr(ticket, "final_category")
            or get_attr(ticket, "ai_suggested_category")
            or "unknown"
        )
        key = (cat, get_attr(ticket, "product"))
        t_date = get_attr(ticket, "date")
        if t_date and t_date >= now - timedelta(hours=48):
            counts_48h[key] += 1

    day_cursor = now - timedelta(days=30)
    while day_cursor < now:
        window_end = day_cursor + timedelta(hours=48)
        window_counter: Counter[tuple[str, str]] = Counter()
        for ticket in tickets:
            t_date = get_attr(ticket, "date")
            if t_date and day_cursor <= t_date < window_end:
                cat = (
                    get_attr(ticket, "final_category")
                    or get_attr(ticket, "ai_suggested_category")
                    or "unknown"
                )
                window_counter[(cat, get_attr(ticket, "product"))] += 1
        for key, cnt in window_counter.items():
            history_counts[key].append(cnt)
        day_cursor += timedelta(days=1)

    anomaly_keys: set[tuple[str, str]] = set()
    for key, count_48h in counts_48h.items():
        history = history_counts.get(key, [])
        if len(history) < 2:
            continue
        avg = sum(history) / len(history)
        variance = sum((x - avg) ** 2 for x in history) / len(history)
        std = math.sqrt(variance)
        if count_48h > avg + 2 * std:
            anomaly_keys.add(key)

    for ticket in tickets:
        tid = ticket_map[ticket.id]
        client = client_by_id.get(ticket.client_id)
        dt = get_attr(ticket, "date")
        closed_at = get_attr(ticket, "closed_at")
        ttr_h = None
        if closed_at and dt:
            ttr_h = (closed_at - dt).total_seconds() / 3600
        cat = (
            get_attr(ticket, "final_category")
            or get_attr(ticket, "ai_suggested_category")
            or "unknown"
        )
        is_anom = 1 if (cat, get_attr(ticket, "product")) in anomaly_keys else 0
        adb.add(
            FactProblems(
                ticket_id=tid,
                date=_to_date(dt),
                hour=dt.hour if dt else None,
                day_of_week=_WEEKDAYS_RU[dt.weekday()] if dt else None,
                product=get_attr(ticket, "product"),
                category=cat,
                priority=_priority_label(ticket),
                city=get_attr(client, "city") if client else None,
                age_group=_age_group(get_attr(client, "age")) if client else None,
                keywords=get_attr(ticket, "keywords"),
                ttr_hours=round(ttr_h, 2) if ttr_h is not None else None,
                is_anomaly=is_anom,
            )
        )

    # ── D6: fact_forecast (optional xlsx from time_series model) ──
    forecast_rows = 0
    if forecast_xlsx and forecast_xlsx.is_file():
        try:
            import pandas as pd

            df = pd.read_excel(forecast_xlsx)
            col_map = {
                "forecast_date": ["forecast_date", "date", "Дата"],
                "category": ["category", "final_category", "Категория"],
                "product": ["product", "Продукт"],
                "predicted_count": ["predicted_count", "predicted", "count", "Прогноз"],
            }

            def _pick(row_cols, names):
                for n in names:
                    if n in row_cols:
                        return n
                return None

            cols = list(df.columns)
            fd = _pick(cols, col_map["forecast_date"])
            cat_c = _pick(cols, col_map["category"])
            prod_c = _pick(cols, col_map["product"])
            pred_c = _pick(cols, col_map["predicted_count"])
            if fd and cat_c and prod_c and pred_c:
                for fid, (_, row) in enumerate(df.iterrows(), start=1):
                    d = pd.to_datetime(row[fd])
                    adb.add(
                        FactForecast(
                            forecast_id=fid,
                            forecast_date=d.date(),
                            category=str(row[cat_c]),
                            product=str(row[prod_c]),
                            predicted_count=float(row[pred_c]),
                        )
                    )
                    forecast_rows += 1
        except Exception:
            pass

    await adb.commit()
    return {
        "general": len(tickets),
        "ai_effective": dialog_id - 1,
        "admin_effective": len(tickets),
        "fact_users": len(clients),
        "fact_reviews": len(reviews),
        "fact_problems": len(tickets),
        "fact_forecast": forecast_rows,
    }
