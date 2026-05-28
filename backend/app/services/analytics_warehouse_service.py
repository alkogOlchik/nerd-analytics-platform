"""Чтение метрик из аналитической витрины (nerd_analytics_db)."""

import logging
from collections import Counter
from datetime import date, datetime

from sqlalchemy import func, select
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
from backend.app.schemas.analytics import (
    AIAccuracyResponse,
    CountItem,
    ReviewKeywordsResponse,
    ReviewSummaryResponse,
    SLAStatsResponse,
    TicketSummaryResponse,
)
from backend.app.schemas.analytics_extended import (
    AdminSLAResponse,
    AdminWorkloadResponse,
    AdminWorkloadItem,
    AIEfficiencyResponse,
    CategoryCountItem,
    DateCountItem,
    DemographicsCountItem,
    HeatmapItem,
    HeatmapResponse,
    ReviewDynamicsItem,
    ReviewDynamicsResponse,
    SLAPriorityItem,
    TicketAnomaliesResponse,
    TicketAnomalyItem,
    TicketDynamicsResponse,
    TicketReopensResponse,
    UserDemographicsResponse,
    UserRetentionResponse,
)
from backend.app.utils.keywords import split_keywords

logger = logging.getLogger(__name__)
_event_log: list[dict] = []


def _date_filters(column, date_from: date | datetime | None, date_to: date | datetime | None):
    clauses = []
    if date_from:
        d = date_from.date() if isinstance(date_from, datetime) else date_from
        clauses.append(column >= d)
    if date_to:
        d = date_to.date() if isinstance(date_to, datetime) else date_to
        clauses.append(column <= d)
    return clauses


async def on_ticket_created(payload: dict) -> None:
    _event_log.append({"event": "ticket.created", **payload})
    logger.info("Analytics received ticket.created: %s", payload)


async def on_ticket_closed(payload: dict) -> None:
    _event_log.append({"event": "ticket.closed", **payload})
    logger.info("Analytics received ticket.closed: %s", payload)


async def tickets_summary(db: AsyncSession) -> TicketSummaryResponse:
    status_rows = await db.execute(select(General.status, func.count()).group_by(General.status))
    product_rows = await db.execute(select(General.product, func.count()).group_by(General.product))
    category_rows = await db.execute(
        select(General.category, func.count())
        .where(General.category.is_not(None))
        .group_by(General.category)
    )
    return TicketSummaryResponse(
        by_status=[CountItem(key=r[0] or "", count=r[1]) for r in status_rows.all()],
        by_product=[CountItem(key=r[0] or "", count=r[1]) for r in product_rows.all()],
        by_category=[CountItem(key=r[0], count=r[1]) for r in category_rows.all()],
    )


async def tickets_sla(db: AsyncSession) -> SLAStatsResponse:
    rows = (await db.execute(select(AdminEffective))).scalars().all()
    total = len(rows)
    breached_ttfr = sum(1 for r in rows if r.ttfr_met == 0)
    breached_ttr = sum(1 for r in rows if r.ttr_met == 0)
    breached = max(breached_ttfr, breached_ttr)
    compliant = total - breached
    rate = (compliant / total * 100) if total else 100.0
    return SLAStatsResponse(
        total=total,
        breached=breached,
        compliant=compliant,
        compliance_rate=round(rate, 2),
    )


async def ai_accuracy(db: AsyncSession) -> AIAccuracyResponse:
    rows = (await db.execute(select(AiEffective))).scalars().all()
    total = len(rows)
    changed = sum(1 for r in rows if r.admin_changed_category == 1)
    accuracy = ((total - changed) / total * 100) if total else 100.0
    return AIAccuracyResponse(
        total_classified=total,
        admin_changed=changed,
        accuracy_rate=round(accuracy, 2),
    )


async def reviews_summary(db: AsyncSession) -> ReviewSummaryResponse:
    rows = (await db.execute(select(FactReviews))).scalars().all()
    total = len(rows)
    avg = sum(r.rating or 0 for r in rows) / total if total else 0.0
    sentiment_counter: Counter[str] = Counter()
    for r in rows:
        if r.sentiment:
            sentiment_counter[r.sentiment] += 1
    return ReviewSummaryResponse(
        average_rating=round(avg, 2),
        total_reviews=total,
        sentiment_distribution=[
            CountItem(key=k, count=v) for k, v in sentiment_counter.items()
        ],
    )


async def reviews_keywords(db: AsyncSession) -> ReviewKeywordsResponse:
    rows = (await db.execute(select(FactReviews))).scalars().all()
    pos_counter: Counter[str] = Counter()
    neg_counter: Counter[str] = Counter()
    for item in rows:
        pos_counter.update(split_keywords(item.keywords_positive))
        neg_counter.update(split_keywords(item.keywords_negative))
    return ReviewKeywordsResponse(
        keywords_positive=[CountItem(key=k, count=v) for k, v in pos_counter.most_common(20)],
        keywords_negative=[CountItem(key=k, count=v) for k, v in neg_counter.most_common(20)],
    )


async def tickets_dynamics(
    db: AsyncSession,
    *,
    date_from: datetime | None,
    date_to: datetime | None,
    product: str | None,
) -> TicketDynamicsResponse:
    query = (
        select(General.created_at, func.count())
        .group_by(General.created_at)
        .order_by(General.created_at)
    )
    for clause in _date_filters(General.created_at, date_from, date_to):
        query = query.where(clause)
    if product:
        query = query.where(General.product == product)
    rows = (await db.execute(query)).all()
    return TicketDynamicsResponse(
        items=[DateCountItem(date=str(r[0]), count=r[1]) for r in rows if r[0]]
    )


async def tickets_reopens(
    db: AsyncSession,
    *,
    date_from: datetime | None,
    date_to: datetime | None,
    product: str | None,
) -> TicketReopensResponse:
    query = select(General)
    for clause in _date_filters(General.created_at, date_from, date_to):
        query = query.where(clause)
    if product:
        query = query.where(General.product == product)
    rows = (await db.execute(query)).scalars().all()
    total_closed = sum(1 for r in rows if r.status == "закрыто")
    total_reopened = sum(1 for r in rows if (r.reopen_count or 0) > 0)
    rate = (total_reopened / total_closed * 100) if total_closed else 0.0
    return TicketReopensResponse(
        total_closed=total_closed,
        total_reopened=total_reopened,
        reopen_rate_pct=round(rate, 2),
    )


async def ai_efficiency(
    db: AsyncSession,
    *,
    date_from: datetime | None,
    date_to: datetime | None,
    product: str | None,
) -> AIEfficiencyResponse:
    query = select(AiEffective)
    for clause in _date_filters(AiEffective.date, date_from, date_to):
        query = query.where(clause)
    if product:
        query = query.where(AiEffective.product == product)
    rows = (await db.execute(query)).scalars().all()
    auto = sum(1 for r in rows if r.is_resolved_by_ai == 1)
    escalated = sum(1 for r in rows if r.escalated_to_human == 1)
    total = auto + escalated
    auto_pct = (auto / total * 100) if total else 0.0
    esc_msgs = [r.msg_count_before_escalation or 0 for r in rows if r.escalated_to_human == 1]
    avg_esc = sum(esc_msgs) / len(esc_msgs) if esc_msgs else 0.0
    esc_cat: Counter[str] = Counter()
    res_cat: Counter[str] = Counter()
    for r in rows:
        cat = r.final_category or r.ai_category_suggested
        if not cat:
            continue
        if r.is_resolved_by_ai == 1:
            res_cat[cat] += 1
        else:
            esc_cat[cat] += 1
    return AIEfficiencyResponse(
        auto_resolved=auto,
        escalated=escalated,
        auto_resolved_pct=round(auto_pct, 2),
        avg_messages_before_escalation=round(avg_esc, 2),
        top_escalated_categories=[
            CategoryCountItem(category=k, count=v) for k, v in esc_cat.most_common(10)
        ],
        top_resolved_categories=[
            CategoryCountItem(category=k, count=v) for k, v in res_cat.most_common(10)
        ],
    )


async def admin_workload(
    db: AsyncSession,
    *,
    date_from: datetime | None,
    date_to: datetime | None,
    product: str | None,
) -> AdminWorkloadResponse:
    query = select(AdminEffective)
    for clause in _date_filters(AdminEffective.date, date_from, date_to):
        query = query.where(clause)
    if product:
        query = query.where(AdminEffective.product == product)
    rows = (await db.execute(query)).scalars().all()
    stats: dict[str, dict] = {}
    for r in rows:
        admin = r.admin or "Не назначен"
        if admin not in stats:
            stats[admin] = {"open": 0, "closed": 0}
        if r.tickets_closed == 1:
            stats[admin]["closed"] += 1
        else:
            stats[admin]["open"] += 1
    items = [
        AdminWorkloadItem(
            employee_id=admin,
            username=admin,
            open_tickets=counts["open"],
            closed_tickets=counts["closed"],
        )
        for admin, counts in stats.items()
    ]
    return AdminWorkloadResponse(items=items)


async def admin_sla(
    db: AsyncSession,
    *,
    date_from: datetime | None,
    date_to: datetime | None,
    product: str | None,
) -> AdminSLAResponse:
    query = select(AdminEffective)
    for clause in _date_filters(AdminEffective.date, date_from, date_to):
        query = query.where(clause)
    if product:
        query = query.where(AdminEffective.product == product)
    rows = (await db.execute(query)).scalars().all()
    by_priority: dict[str, list] = {}
    violated: Counter[str] = Counter()
    for r in rows:
        by_priority.setdefault(r.priority or "Обычный", []).append(r)
        if r.ttfr_met == 0 and r.category:
            violated[r.category] += 1
    priority_items = []
    for priority, group in by_priority.items():
        ttfr_vals = [g.ttfr_min for g in group if g.ttfr_min is not None]
        ttr_vals = [g.ttr_min for g in group if g.ttr_min is not None]
        ttfr_checks = [g.ttfr_met == 1 for g in group if g.ttfr_met is not None]
        ttr_checks = [g.ttr_met == 1 for g in group if g.ttr_met is not None]
        priority_items.append(
            SLAPriorityItem(
                priority=priority,
                avg_ttfr=round(sum(ttfr_vals) / len(ttfr_vals), 2) if ttfr_vals else 0.0,
                avg_ttr=round(sum(ttr_vals) / len(ttr_vals), 2) if ttr_vals else 0.0,
                sla_ttfr_compliance_pct=round(sum(ttfr_checks) / len(ttfr_checks) * 100, 2)
                if ttfr_checks
                else 0.0,
                sla_ttr_compliance_pct=round(sum(ttr_checks) / len(ttr_checks) * 100, 2)
                if ttr_checks
                else 0.0,
            )
        )
    return AdminSLAResponse(
        by_priority=priority_items,
        top_violated_categories=[
            CategoryCountItem(category=k, count=v) for k, v in violated.most_common(10)
        ],
    )


async def admin_heatmap(
    db: AsyncSession,
    *,
    date_from: datetime | None,
    date_to: datetime | None,
    product: str | None,
) -> HeatmapResponse:
    query = select(AdminEffective).where(AdminEffective.ttfr_min.is_not(None))
    for clause in _date_filters(AdminEffective.date, date_from, date_to):
        query = query.where(clause)
    if product:
        query = query.where(AdminEffective.product == product)
    rows = (await db.execute(query)).scalars().all()
    buckets: dict[tuple[int, int], list[float]] = {}
    for r in rows:
        if r.hour is None:
            continue
        dow = 0
        if r.day_of_week and r.day_of_week in (
            "Понедельник",
            "Вторник",
            "Среда",
            "Четверг",
            "Пятница",
            "Суббота",
            "Воскресенье",
        ):
            dow = [
                "Понедельник",
                "Вторник",
                "Среда",
                "Четверг",
                "Пятница",
                "Суббота",
                "Воскресенье",
            ].index(r.day_of_week)
        buckets.setdefault((dow, r.hour), []).append(r.ttfr_min)
    items = [
        HeatmapItem(day_of_week=dow, hour=hour, avg_ttfr_min=round(sum(vals) / len(vals), 2))
        for (dow, hour), vals in buckets.items()
    ]
    return HeatmapResponse(items=items)


async def users_demographics(db: AsyncSession, *, product: str | None) -> UserDemographicsResponse:
    if product:
        query = select(FactUsers).where(FactUsers.product.any(product))
        rows = (await db.execute(query)).scalars().all()
    else:
        rows = (await db.execute(select(FactUsers))).scalars().all()
    gender_c: Counter[str] = Counter()
    age_c: Counter[str] = Counter()
    city_c: Counter[str] = Counter()
    for u in rows:
        if u.gender:
            gender_c[u.gender] += 1
        if u.age_group:
            age_c[u.age_group] += 1
        if u.city:
            city_c[u.city] += 1
    return UserDemographicsResponse(
        by_gender=[DemographicsCountItem(key=k, count=v) for k, v in gender_c.items()],
        by_age_group=[DemographicsCountItem(key=k, count=v) for k, v in age_c.items()],
        by_city=[DemographicsCountItem(key=k, count=v) for k, v in city_c.most_common(10)],
    )


async def users_retention(
    db: AsyncSession,
    *,
    date_from: datetime | None,
    date_to: datetime | None,
    product: str | None,
) -> UserRetentionResponse:
    query = select(FactUsers)
    rows = (await db.execute(query)).scalars().all()
    total = len(rows)
    r7 = sum(1 for u in rows if u.retention_7d == 1)
    r14 = sum(1 for u in rows if u.retention_14d == 1)
    r30 = sum(1 for u in rows if u.retention_30d == 1)

    def pct(n: int) -> float:
        return round(n / total * 100, 2) if total else 0.0

    return UserRetentionResponse(
        retention_7d_pct=pct(r7),
        retention_14d_pct=pct(r14),
        retention_30d_pct=pct(r30),
    )


async def reviews_dynamics(
    db: AsyncSession,
    *,
    date_from: datetime | None,
    date_to: datetime | None,
    product: str | None,
) -> ReviewDynamicsResponse:
    query = select(FactReviews)
    for clause in _date_filters(FactReviews.date, date_from, date_to):
        query = query.where(clause)
    if product:
        query = query.where(FactReviews.product == product)
    rows = (await db.execute(query)).scalars().all()
    by_date: dict[date, dict] = {}
    for r in rows:
        if not r.date:
            continue
        bucket = by_date.setdefault(r.date, {"pos": 0, "neg": 0})
        if (r.rating or 0) >= 4:
            bucket["pos"] += 1
        if (r.rating or 0) <= 2:
            bucket["neg"] += 1
    items = [
        ReviewDynamicsItem(
            date=str(d),
            positive_count=v["pos"],
            negative_count=v["neg"],
        )
        for d, v in sorted(by_date.items())
    ]
    return ReviewDynamicsResponse(items=items)


async def tickets_anomalies(
    db: AsyncSession,
    *,
    product: str | None,
) -> TicketAnomaliesResponse:
    query = select(FactProblems).where(FactProblems.is_anomaly == 1)
    if product:
        query = query.where(FactProblems.product == product)
    rows = (await db.execute(query)).scalars().all()
    by_key: Counter[tuple[str, str]] = Counter()
    for r in rows:
        by_key[(r.category or "unknown", r.product or "")] += 1
    items = [
        TicketAnomalyItem(
            category=cat,
            product=prod,
            count_48h=cnt,
            rolling_avg=0.0,
            stddev=0.0,
            z_score=0.0,
        )
        for (cat, prod), cnt in by_key.items()
    ]
    return TicketAnomaliesResponse(items=items)


async def tickets_forecast(
    db: AsyncSession,
    *,
    product: str | None = None,
    category: str | None = None,
) -> list[dict]:
    query = select(FactForecast)
    if product:
        query = query.where(FactForecast.product == product)
    if category:
        query = query.where(FactForecast.category == category)
    query = query.order_by(FactForecast.forecast_date)
    rows = (await db.execute(query)).scalars().all()
    return [
        {
            "forecast_id": r.forecast_id,
            "forecast_date": str(r.forecast_date),
            "category": r.category,
            "product": r.product,
            "predicted_count": r.predicted_count,
        }
        for r in rows
    ]
