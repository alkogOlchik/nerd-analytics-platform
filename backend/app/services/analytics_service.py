"""Аналитика по операционной БД nerd_db (дашборды /analytics/dashboard/*)."""

from __future__ import annotations

import logging
import statistics
import uuid
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import case, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.chat import ChatHistory
from backend.app.models.enums import ChatRole, TicketStatus
from backend.app.models.review import Review
from backend.app.models.ticket import Ticket
from backend.app.models.user import Client, Employee
from backend.app.schemas.analytics import (
    AIAccuracyResponse,
    CountItem,
    ReviewKeywordsResponse,
    ReviewSummaryResponse,
    SLAStatsResponse,
    TicketSummaryResponse,
)
from backend.app.schemas.analytics_extended import (
    AIEfficiencyResponse,
    AdminSLAResponse,
    AdminWorkloadItem,
    AdminWorkloadResponse,
    CategoryCountItem as ExtCategoryCountItem,
    DateCountItem as ExtDateCountItem,
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
from backend.app.schemas.analytics_dashboards import (
    AdminSatisfactionItem,
    CategoryCountItem,
    ClassificationAccuracyItem,
    Dashboard1Response,
    Dashboard2Response,
    Dashboard3Response,
    Dashboard4Response,
    Dashboard5Response,
    Dashboard6ForecastResponse,
    Dashboard6TicketsResponse,
    DateAutoPctItem,
    DateCountItem,
    DateFloatItem,
    DateSentimentItem,
    DemographicsItem,
    ForecastItem,
    HeatmapCountItem,
    HeatmapTtfrItem,
    LatestNegativeReviewItem,
    LeaderboardItem,
    PriorityAvgItem,
    ProductRatingItem,
    RetentionBlock,
    SlaComplianceItem,
    SlowestCategoryItem,
    TicketAnomalyItem,
    TopActiveUserItem,
    WordCountItem,
    WorkloadItem,
)
from backend.app.utils.keywords import split_keywords

logger = logging.getLogger(__name__)

ACTIVE_STATUSES = {
    TicketStatus.accepted.value,
    TicketStatus.in_progress.value,
    TicketStatus.needs_info.value,
    TicketStatus.dev_handoff.value,
}


@dataclass(frozen=True)
class AnalyticsFilters:
    date_from: datetime
    date_to: datetime
    product: str | None
    priority: str | None
    category: str | None


def resolve_filters(
    *,
    date_from: datetime | None,
    date_to: datetime | None,
    product: str | None,
    priority: str | None,
    category: str | None,
) -> AnalyticsFilters:
    now = datetime.now(UTC)
    end = date_to or now
    start = date_from or (end - timedelta(days=30))
    if start.tzinfo is None:
        start = start.replace(tzinfo=UTC)
    if end.tzinfo is None:
        end = end.replace(tzinfo=UTC)
    return AnalyticsFilters(
        date_from=start,
        date_to=end,
        product=product,
        priority=priority,
        category=category,
    )


def _previous_period(filters: AnalyticsFilters) -> tuple[datetime, datetime]:
    delta = filters.date_to - filters.date_from
    prev_to = filters.date_from - timedelta(microseconds=1)
    prev_from = prev_to - delta
    return prev_from, prev_to


def _ticket_where(filters: AnalyticsFilters, *, use_date: bool = True):
    clauses = []
    if use_date:
        clauses.append(Ticket.date >= filters.date_from)
        clauses.append(Ticket.date <= filters.date_to)
    if filters.product:
        clauses.append(Ticket.product == filters.product)
    if filters.priority:
        clauses.append(Ticket.priority == filters.priority)
    if filters.category:
        clauses.append(
            or_(
                Ticket.final_category == filters.category,
                Ticket.ai_suggested_category == filters.category,
            )
        )
    return clauses


def _review_where(filters: AnalyticsFilters):
    clauses = [
        Review.created_at >= filters.date_from,
        Review.created_at <= filters.date_to,
    ]
    if filters.product:
        clauses.append(Review.product == filters.product)
    if filters.category:
        clauses.append(
            or_(
                Review.final_category == filters.category,
                Review.ai_suggested_category == filters.category,
            )
        )
    return clauses


def _count_keywords(rows: list[str], limit: int = 20) -> list[WordCountItem]:
    counter: Counter[str] = Counter()
    for raw in rows:
        counter.update(split_keywords(raw))
    return [WordCountItem(word=w, count=c) for w, c in counter.most_common(limit)]


def _age_group(age: int | None) -> str:
    if age is None:
        return "не указан"
    if age < 18:
        return "до 18"
    if age <= 25:
        return "18-25"
    if age <= 35:
        return "26-35"
    if age <= 45:
        return "36-45"
    if age <= 55:
        return "46-55"
    return "56+"


async def dashboard_1(db: AsyncSession, filters: AnalyticsFilters) -> Dashboard1Response:
    ticket_clauses = _ticket_where(filters)
    prev_from, prev_to = _previous_period(filters)

    dyn_rows = (
        await db.execute(
            select(func.date(Ticket.date), func.count())
            .where(*ticket_clauses)
            .group_by(func.date(Ticket.date))
            .order_by(func.date(Ticket.date))
        )
    ).all()
    dynamics = [DateCountItem(date=str(r[0]), count=r[1]) for r in dyn_rows]

    total = (
        await db.execute(select(func.count()).select_from(Ticket).where(*ticket_clauses))
    ).scalar_one()

    prev_clauses = [
        Ticket.date >= prev_from,
        Ticket.date <= prev_to,
        *([Ticket.product == filters.product] if filters.product else []),
        *([Ticket.priority == filters.priority] if filters.priority else []),
    ]
    if filters.category:
        prev_clauses.append(
            or_(
                Ticket.final_category == filters.category,
                Ticket.ai_suggested_category == filters.category,
            )
        )
    prev_total = (
        await db.execute(select(func.count()).select_from(Ticket).where(*prev_clauses))
    ).scalar_one()
    delta_pct = ((total - prev_total) / prev_total * 100) if prev_total else 0.0

    active_clauses = [Ticket.status.in_(ACTIVE_STATUSES), *_ticket_where(filters, use_date=False)]
    active = (
        await db.execute(select(func.count()).select_from(Ticket).where(*active_clauses))
    ).scalar_one()

    prio_rows = (
        await db.execute(
            select(Ticket.priority, func.count())
            .where(*active_clauses)
            .group_by(Ticket.priority)
        )
    ).all()
    active_by_priority = {str(r[0]): r[1] for r in prio_rows}

    avg_life = (
        await db.execute(
            select(
                func.avg(
                    func.extract("epoch", Ticket.closed_at - Ticket.date) / 3600.0
                )
            ).where(
                *ticket_clauses,
                Ticket.closed_at.is_not(None),
            )
        )
    ).scalar_one()

    reopen_rows = (
        await db.execute(
            select(func.date(Ticket.last_reopened_at), func.count())
            .where(
                *ticket_clauses,
                Ticket.reopened_count > 0,
                Ticket.last_reopened_at.is_not(None),
            )
            .group_by(func.date(Ticket.last_reopened_at))
            .order_by(func.date(Ticket.last_reopened_at))
        )
    ).all()
    reopens_dynamics = [DateCountItem(date=str(r[0]), count=r[1]) for r in reopen_rows if r[0]]

    closed_count = (
        await db.execute(
            select(func.count()).where(*ticket_clauses, Ticket.closed_at.is_not(None))
        )
    ).scalar_one()
    reopened_count = (
        await db.execute(
            select(func.count()).where(*ticket_clauses, Ticket.reopened_count > 0)
        )
    ).scalar_one()
    reopen_rate = (reopened_count / closed_count * 100) if closed_count else 0.0

    sat_rows = (
        await db.execute(
            select(func.date(Review.created_at), func.avg(Review.rating))
            .where(*_review_where(filters))
            .group_by(func.date(Review.created_at))
            .order_by(func.date(Review.created_at))
        )
    ).all()
    satisfaction_dynamics = [
        DateFloatItem(date=str(r[0]), avg_rating=round(float(r[1] or 0), 2)) for r in sat_rows if r[0]
    ]

    rating_rows = (
        await db.execute(
            select(Review.rating, func.count())
            .where(*_review_where(filters))
            .group_by(Review.rating)
        )
    ).all()
    rating_distribution = {str(int(r[0])): r[1] for r in rating_rows}

    worst_rows = (
        await db.execute(
            select(Review.product, func.avg(Review.rating))
            .where(*_review_where(filters), Review.product.is_not(None))
            .group_by(Review.product)
            .order_by(func.avg(Review.rating))
            .limit(5)
        )
    ).all()
    worst_products = [
        ProductRatingItem(product=str(r[0]), avg_rating=round(float(r[1] or 0), 2)) for r in worst_rows
    ]

    return Dashboard1Response(
        dynamics=dynamics,
        total_tickets=total or 0,
        total_tickets_delta_pct=round(delta_pct, 2),
        active_tickets=active or 0,
        active_by_priority=active_by_priority,
        avg_lifetime_hours=round(float(avg_life or 0), 2),
        reopens_dynamics=reopens_dynamics,
        reopen_rate_pct=round(reopen_rate, 2),
        satisfaction_dynamics=satisfaction_dynamics,
        rating_distribution=rating_distribution,
        worst_products=worst_products,
    )


async def dashboard_2(db: AsyncSession, filters: AnalyticsFilters) -> Dashboard2Response:
    chat_clauses = [
        ChatHistory.created_at >= filters.date_from,
        ChatHistory.created_at <= filters.date_to,
    ]
    if filters.product:
        chat_clauses.append(ChatHistory.product == filters.product)
    if filters.category:
        chat_clauses.append(
            or_(
                ChatHistory.category == filters.category,
            )
        )

    chats = (await db.execute(select(ChatHistory).where(*chat_clauses))).scalars().all()

    by_chat: dict[uuid.UUID, list[ChatHistory]] = defaultdict(list)
    for msg in chats:
        by_chat[msg.chat_id].append(msg)

    def chat_auto_resolved(messages: list[ChatHistory]) -> bool:
        return any(m.resolved_by_ai for m in messages)

    def chat_escalated(messages: list[ChatHistory]) -> bool:
        return any(not m.resolved_by_ai for m in messages) and any(m.ticket_id for m in messages)

    auto_by_date: dict[str, set[uuid.UUID]] = defaultdict(set)
    total_by_date: dict[str, set[uuid.UUID]] = defaultdict(set)
    for cid, msgs in by_chat.items():
        day = min(m.created_at for m in msgs).date().isoformat()
        total_by_date[day].add(cid)
        if chat_auto_resolved(msgs):
            auto_by_date[day].add(cid)

    auto_resolved_dynamics = [
        DateAutoPctItem(
            date=day,
            auto_pct=round(len(auto_by_date[day]) / len(total_by_date[day]) * 100, 2)
            if total_by_date[day]
            else 0.0,
        )
        for day in sorted(total_by_date)
    ]

    auto_chats = [cid for cid, msgs in by_chat.items() if chat_auto_resolved(msgs)]
    esc_chats = [cid for cid, msgs in by_chat.items() if chat_escalated(msgs)]
    total_chats = len(by_chat)
    current_auto_pct = (len(auto_chats) / total_chats * 100) if total_chats else 0.0

    week_ago = filters.date_to - timedelta(days=7)
    prev_auto = 0
    prev_total = 0
    for cid, msgs in by_chat.items():
        first = min(m.created_at for m in msgs)
        if week_ago <= first <= filters.date_to - timedelta(days=7):
            prev_total += 1
            if chat_auto_resolved(msgs):
                prev_auto += 1
    prev_pct = (prev_auto / prev_total * 100) if prev_total else 0.0
    auto_delta = current_auto_pct - prev_pct

    esc_cat: Counter[str] = Counter()
    ai_cat: Counter[str] = Counter()
    esc_msg_counts: list[int] = []
    ai_durations: list[float] = []

    for cid, msgs in by_chat.items():
        msgs_sorted = sorted(msgs, key=lambda m: m.created_at)
        cat = next((m.category for m in msgs_sorted if m.category), None) or "без категории"
        if chat_escalated(msgs_sorted):
            esc_cat[cat] += 1
            client_msgs = [m for m in msgs_sorted if m.role == ChatRole.client.value]
            esc_msg_counts.append(len(client_msgs) if client_msgs else len(msgs_sorted))
        elif chat_auto_resolved(msgs_sorted):
            ai_cat[cat] += 1
            if len(msgs_sorted) >= 2:
                span = (msgs_sorted[-1].created_at - msgs_sorted[0].created_at).total_seconds() / 60
                ai_durations.append(span)

    ticket_clauses = _ticket_where(filters)
    human_avg = (
        await db.execute(
            select(
                func.avg(func.extract("epoch", Ticket.closed_at - Ticket.date) / 60.0)
            ).where(*ticket_clauses, Ticket.closed_at.is_not(None))
        )
    ).scalar_one()

    class_rows = (
        await db.execute(
            select(
                Ticket.final_category,
                func.count(),
                func.sum(case((Ticket.is_admin_changed.is_(True), 1), else_=0)),
            )
            .where(*ticket_clauses, Ticket.final_category.is_not(None))
            .group_by(Ticket.final_category)
        )
    ).all()

    classification_accuracy = []
    for row in class_rows:
        cat, total, changed = row[0], row[1], int(row[2] or 0)
        acc = ((total - changed) / total * 100) if total else 100.0
        classification_accuracy.append(
            ClassificationAccuracyItem(
                category=cat,
                total=total,
                changed=changed,
                accuracy_pct=round(acc, 2),
            )
        )

    return Dashboard2Response(
        auto_resolved_dynamics=auto_resolved_dynamics,
        current_auto_resolved_pct=round(current_auto_pct, 2),
        auto_resolved_delta_pct=round(auto_delta, 2),
        top_escalated_categories=[
            CategoryCountItem(category=k, count=v) for k, v in esc_cat.most_common(10)
        ],
        avg_time_ai_min=round(sum(ai_durations) / len(ai_durations), 2) if ai_durations else 0.0,
        avg_time_human_min=round(float(human_avg or 0), 2),
        top_ai_resolved_categories=[
            CategoryCountItem(category=k, count=v) for k, v in ai_cat.most_common(10)
        ],
        avg_messages_before_escalation=round(
            sum(esc_msg_counts) / len(esc_msg_counts), 2
        )
        if esc_msg_counts
        else 0.0,
        classification_accuracy=classification_accuracy,
    )


async def _first_admin_reply(db: AsyncSession, ticket_ids: list[uuid.UUID]) -> dict[uuid.UUID, datetime]:
    if not ticket_ids:
        return {}
    rows = (
        await db.execute(
            select(ChatHistory.ticket_id, func.min(ChatHistory.created_at))
            .where(
                ChatHistory.ticket_id.in_(ticket_ids),
                ChatHistory.role == ChatRole.admin.value,
            )
            .group_by(ChatHistory.ticket_id)
        )
    ).all()
    return {r[0]: r[1] for r in rows if r[0]}


async def dashboard_3(db: AsyncSession, filters: AnalyticsFilters) -> Dashboard3Response:
    ticket_clauses = _ticket_where(filters)
    tickets = (await db.execute(select(Ticket).where(*ticket_clauses))).scalars().all()
    ticket_ids = [t.id for t in tickets]
    first_admin = await _first_admin_reply(db, ticket_ids)

    employees = {
        e.id: e
        for e in (await db.execute(select(Employee))).scalars().all()
    }

    workload_map: dict[uuid.UUID, dict[str, int]] = defaultdict(lambda: {"open": 0, "closed": 0})
    ttfr_by_prio: dict[str, list[float]] = defaultdict(list)
    ttr_by_prio: dict[str, list[float]] = defaultdict(list)
    ttfr_ok: dict[str, list[bool]] = defaultdict(list)
    ttr_ok: dict[str, list[bool]] = defaultdict(list)
    violated_cat: Counter[str] = Counter()
    heat_ttfr: dict[tuple[int, int], list[float]] = defaultdict(list)

    for t in tickets:
        emp_id = t.responsible_id
        if not emp_id:
            continue
        bucket = workload_map[emp_id]
        if t.closed_at:
            bucket["closed"] += 1
        elif t.status in ACTIVE_STATUSES:
            bucket["open"] += 1

        prio = t.priority or "medium"
        if t.closed_at:
            ttr_min = (t.closed_at - t.date).total_seconds() / 60
            ttr_by_prio[prio].append(ttr_min)
            if t.sla_ttr_min:
                ttr_ok[prio].append(ttr_min <= t.sla_ttr_min)
            if t.ttfr_met is False or (t.sla_ttfr_min and t.closed_at):
                pass

        admin_at = first_admin.get(t.id)
        if admin_at:
            ttfr_min = (admin_at - t.date).total_seconds() / 60
            ttfr_by_prio[prio].append(ttfr_min)
            if t.sla_ttfr_min:
                ttfr_ok[prio].append(ttfr_min <= t.sla_ttfr_min)
            dow = admin_at.weekday()
            hour = admin_at.hour
            heat_ttfr[(dow, hour)].append(ttfr_min)

        if t.sla_ttfr_min and admin_at:
            ttfr_min = (admin_at - t.date).total_seconds() / 60
            if ttfr_min > t.sla_ttfr_min and t.final_category:
                violated_cat[t.final_category] += 1
        if t.closed_at and t.sla_ttr_min:
            ttr_min = (t.closed_at - t.date).total_seconds() / 60
            if ttr_min > t.sla_ttr_min and t.final_category:
                violated_cat[t.final_category] += 1

    workload = []
    for emp_id, counts in workload_map.items():
        emp = employees.get(emp_id)
        workload.append(
            WorkloadItem(
                employee_id=str(emp_id),
                username=emp.username if emp else str(emp_id),
                open=counts["open"],
                closed=counts["closed"],
            )
        )

    leaderboard = []
    for emp_id, counts in workload_map.items():
        emp = employees.get(emp_id)
        ttfr_vals = []
        ttr_vals = []
        sla_hits = []
        for t in tickets:
            if t.responsible_id != emp_id:
                continue
            admin_at = first_admin.get(t.id)
            if admin_at:
                ttfr_vals.append((admin_at - t.date).total_seconds() / 60)
            if t.closed_at:
                ttr_vals.append((t.closed_at - t.date).total_seconds() / 60)
                ok_ttfr = True
                ok_ttr = True
                if t.sla_ttfr_min and admin_at:
                    ok_ttfr = (admin_at - t.date).total_seconds() / 60 <= t.sla_ttfr_min
                if t.sla_ttr_min:
                    ok_ttr = (t.closed_at - t.date).total_seconds() / 60 <= t.sla_ttr_min
                sla_hits.append(ok_ttfr and ok_ttr)
        leaderboard.append(
            LeaderboardItem(
                employee_id=str(emp_id),
                username=emp.username if emp else str(emp_id),
                closed_count=counts["closed"],
                avg_ttfr_min=round(sum(ttfr_vals) / len(ttfr_vals), 2) if ttfr_vals else 0.0,
                avg_ttr_min=round(sum(ttr_vals) / len(ttr_vals), 2) if ttr_vals else 0.0,
                sla_pct=round(sum(sla_hits) / len(sla_hits) * 100, 2) if sla_hits else 0.0,
            )
        )
    leaderboard.sort(key=lambda x: x.closed_count, reverse=True)

    ttfr_by_priority = [
        PriorityAvgItem(priority=p, avg_min=round(sum(v) / len(v), 2))
        for p, v in ttfr_by_prio.items()
        if v
    ]
    ttr_by_priority = [
        PriorityAvgItem(priority=p, avg_min=round(sum(v) / len(v), 2))
        for p, v in ttr_by_prio.items()
        if v
    ]
    sla_compliance = [
        SlaComplianceItem(
            priority=p,
            ttfr_ok_pct=round(sum(ttfr_ok[p]) / len(ttfr_ok[p]) * 100, 2) if ttfr_ok[p] else 0.0,
            ttr_ok_pct=round(sum(ttr_ok[p]) / len(ttr_ok[p]) * 100, 2) if ttr_ok[p] else 0.0,
        )
        for p in set(ttfr_ok) | set(ttr_ok)
    ]

    heatmap = [
        HeatmapTtfrItem(
            day_of_week=dow,
            hour=hour,
            avg_ttfr_min=round(sum(vals) / len(vals), 2),
        )
        for (dow, hour), vals in heat_ttfr.items()
    ]

    review_rows = (
        await db.execute(
            select(Ticket.responsible_id, func.avg(Review.rating), func.count())
            .join(Review, Review.ticket_id == Ticket.id)
            .where(*_review_where(filters), Ticket.responsible_id.is_not(None))
            .group_by(Ticket.responsible_id)
        )
    ).all()
    satisfaction_by_admin = []
    for row in review_rows:
        emp_id, avg_rating, _ = row
        emp = employees.get(emp_id)
        satisfaction_by_admin.append(
            AdminSatisfactionItem(
                employee_id=str(emp_id),
                username=emp.username if emp else str(emp_id),
                avg_rating=round(float(avg_rating or 0), 2),
            )
        )

    return Dashboard3Response(
        workload=workload,
        leaderboard=leaderboard,
        ttfr_by_priority=ttfr_by_priority,
        ttr_by_priority=ttr_by_priority,
        sla_compliance=sla_compliance,
        sla_violations_by_category=[
            CategoryCountItem(category=k, count=v) for k, v in violated_cat.most_common(10)
        ],
        heatmap=heatmap,
        satisfaction_by_admin=satisfaction_by_admin,
    )


async def dashboard_4(db: AsyncSession, filters: AnalyticsFilters) -> Dashboard4Response:
    total_users = (await db.execute(select(func.count()).select_from(Client))).scalar_one()

    new_users = (
        await db.execute(
            select(func.count())
            .select_from(Client)
            .where(
                Client.created_at >= filters.date_from,
                Client.created_at <= filters.date_to,
            )
        )
    ).scalar_one()

    ticket_clauses = _ticket_where(filters)
    active_rows = (
        await db.execute(
            select(
                Ticket.client_id,
                func.count(),
                func.sum(case((Ticket.status.in_(ACTIVE_STATUSES), 1), else_=0)),
            )
            .where(*ticket_clauses)
            .group_by(Ticket.client_id)
            .order_by(func.count().desc())
            .limit(10)
        )
    ).all()
    top_active_users = [
        TopActiveUserItem(
            client_id=str(r[0]),
            ticket_count=r[1],
            open_count=int(r[2] or 0),
        )
        for r in active_rows
    ]

    clients = (await db.execute(select(Client))).scalars().all()
    gender_counter: Counter[str] = Counter()
    age_counter: Counter[str] = Counter()
    city_counter: Counter[str] = Counter()
    for c in clients:
        gender_counter[c.gender or "не указан"] += 1
        age_counter[_age_group(c.age)] += 1
        city_counter[c.city or "не указан"] += 1

    tickets_all = (
        await db.execute(
            select(Ticket.client_id, Ticket.date)
            .where(*ticket_clauses)
            .order_by(Ticket.client_id, Ticket.date)
        )
    ).all()
    by_client: dict[uuid.UUID, list[datetime]] = defaultdict(list)
    for client_id, dt in tickets_all:
        by_client[client_id].append(dt)

    def retention_pct(days: int) -> float:
        eligible = 0
        retained = 0
        for dates in by_client.values():
            if len(dates) < 2:
                continue
            dates_sorted = sorted(dates)
            eligible += 1
            second = dates_sorted[1]
            if (second - dates_sorted[0]).days <= days:
                retained += 1
        return round(retained / eligible * 100, 2) if eligible else 0.0

    return Dashboard4Response(
        total_users=total_users or 0,
        new_users_period=new_users or 0,
        top_active_users=top_active_users,
        by_gender=[DemographicsItem(gender=k, count=v) for k, v in gender_counter.items()],
        by_age_group=[DemographicsItem(group=k, count=v) for k, v in age_counter.items()],
        by_city=[DemographicsItem(city=k, count=v) for k, v in city_counter.most_common(20)],
        retention=RetentionBlock(
            d7_pct=retention_pct(7),
            d14_pct=retention_pct(14),
            d30_pct=retention_pct(30),
        ),
    )


async def dashboard_5(db: AsyncSession, filters: AnalyticsFilters) -> Dashboard5Response:
    reviews = (await db.execute(select(Review).where(*_review_where(filters)))).scalars().all()

    pos_kw = [r.keywords_positive or "" for r in reviews]
    neg_kw = [r.keywords_negative or "" for r in reviews]
    cat_counter: Counter[str] = Counter()
    rating_dist: Counter[int] = Counter()
    by_date: dict[str, dict[str, int]] = defaultdict(lambda: {"positive": 0, "negative": 0})

    for r in reviews:
        cat = r.final_category or r.ai_suggested_category
        if cat:
            cat_counter[cat] += 1
        rating_dist[r.rating] += 1
        day = r.created_at.date().isoformat()
        if r.rating >= 4:
            by_date[day]["positive"] += 1
        if r.rating <= 2:
            by_date[day]["negative"] += 1

    positive_total = sum(1 for r in reviews if r.rating >= 4)
    pos_share = (positive_total / len(reviews) * 100) if reviews else 0.0

    latest_neg = sorted(
        [r for r in reviews if r.rating <= 2],
        key=lambda r: r.created_at,
        reverse=True,
    )[:10]

    return Dashboard5Response(
        top_keywords_positive=_count_keywords(pos_kw),
        top_keywords_negative=_count_keywords(neg_kw),
        top_categories=[
            CategoryCountItem(category=k, count=v) for k, v in cat_counter.most_common(10)
        ],
        sentiment_dynamics=[
            DateSentimentItem(date=d, positive=v["positive"], negative=v["negative"])
            for d, v in sorted(by_date.items())
        ],
        positive_share_pct=round(pos_share, 2),
        rating_distribution={str(k): v for k, v in sorted(rating_dist.items())},
        latest_negative=[
            LatestNegativeReviewItem(
                review_id=str(r.id),
                ticket_id=str(r.ticket_id) if r.ticket_id else None,
                comment=r.comment,
                rating=r.rating,
                created_at=r.created_at.isoformat(),
            )
            for r in latest_neg
        ],
    )


async def dashboard_6_tickets(
    db: AsyncSession, filters: AnalyticsFilters
) -> Dashboard6TicketsResponse:
    ticket_clauses = _ticket_where(filters)
    tickets = (await db.execute(select(Ticket).where(*ticket_clauses))).scalars().all()

    kw_rows = [t.keywords or "" for t in tickets if t.keywords]
    cat_counter: Counter[str] = Counter()
    for t in tickets:
        cat = t.final_category or t.ai_suggested_category
        if cat:
            cat_counter[cat] += 1

    dyn_counter: Counter[str] = Counter()
    heat_counter: Counter[tuple[int, int]] = Counter()
    city_counter: Counter[str] = Counter()
    age_counter: Counter[str] = Counter()
    slow_acc: dict[str, list[float]] = defaultdict(list)

    client_ids = {t.client_id for t in tickets}
    clients = {}
    if client_ids:
        for c in (await db.execute(select(Client).where(Client.id.in_(client_ids)))).scalars():
            clients[c.id] = c

    for t in tickets:
        dyn_counter[t.date.date().isoformat()] += 1
        heat_counter[(t.date.weekday(), t.date.hour)] += 1
        if t.closed_at:
            cat = t.final_category or t.ai_suggested_category or "без категории"
            slow_acc[cat].append((t.closed_at - t.date).total_seconds() / 60)
        c = clients.get(t.client_id)
        if c:
            city_counter[c.city or "не указан"] += 1
            age_counter[_age_group(c.age)] += 1

    now = datetime.now(UTC)
    window_48h = now - timedelta(hours=48)
    recent = [t for t in tickets if t.date >= window_48h]
    recent_counts: Counter[tuple[str, str]] = Counter()
    for t in recent:
        cat = t.final_category or t.ai_suggested_category or "без категории"
        recent_counts[(cat, t.product)] += 1

    daily_history: dict[tuple[str, str], list[int]] = defaultdict(list)
    thirty_days_ago = now - timedelta(days=30)
    for t in tickets:
        if t.date >= thirty_days_ago:
            cat = t.final_category or t.ai_suggested_category or "без категории"
            daily_history[(cat, t.product)].append(1)

    daily_by_key: dict[tuple[str, str], Counter[str]] = defaultdict(Counter)
    for t in tickets:
        if t.date >= thirty_days_ago:
            key = (t.final_category or t.ai_suggested_category or "без категории", t.product)
            daily_by_key[key][t.date.date().isoformat()] += 1

    anomalies: list[TicketAnomalyItem] = []
    for (cat, product), count_48h in recent_counts.items():
        daily_counts = list(daily_by_key[(cat, product)].values())
        if len(daily_counts) < 2:
            continue
        avg = statistics.mean(daily_counts)
        std = statistics.pstdev(daily_counts) if len(daily_counts) > 1 else 1.0
        z = (count_48h - avg) / std if std else 0.0
        if z > 2:
            anomalies.append(
                TicketAnomalyItem(
                    category=cat,
                    product=product,
                    count_48h=count_48h,
                    rolling_avg=round(avg, 2),
                    z_score=round(z, 2),
                )
            )
    anomalies.sort(key=lambda a: a.z_score, reverse=True)

    return Dashboard6TicketsResponse(
        top_keywords=_count_keywords(kw_rows),
        top_categories=[
            CategoryCountItem(category=k, count=v) for k, v in cat_counter.most_common(10)
        ],
        dynamics=[
            DateCountItem(date=d, count=c) for d, c in sorted(dyn_counter.items())
        ],
        anomalies=anomalies,
        by_city=[DemographicsItem(city=k, count=v) for k, v in city_counter.most_common(15)],
        by_age_group=[DemographicsItem(group=k, count=v) for k, v in age_counter.items()],
        heatmap=[
            HeatmapCountItem(day_of_week=dow, hour=hour, count=cnt)
            for (dow, hour), cnt in heat_counter.items()
        ],
        slowest_categories=[
            SlowestCategoryItem(category=k, avg_ttr_min=round(sum(v) / len(v), 2))
            for k, v in slow_acc.items()
            if v
        ],
    )


async def dashboard_6_forecast(
    db: AsyncSession,
    *,
    product: str | None,
    category: str | None,
) -> Dashboard6ForecastResponse:
    now = datetime.now(UTC)
    start = now - timedelta(days=30)
    clauses = [Ticket.date >= start]
    if product:
        clauses.append(Ticket.product == product)
    if category:
        clauses.append(
            or_(
                Ticket.final_category == category,
                Ticket.ai_suggested_category == category,
            )
        )

    rows = (
        await db.execute(
            select(func.date(Ticket.date), func.count())
            .where(*clauses)
            .group_by(func.date(Ticket.date))
            .order_by(func.date(Ticket.date))
        )
    ).all()
    daily = [r[1] for r in rows]
    if not daily:
        return Dashboard6ForecastResponse(forecast=[])

    window = daily[-7:] if len(daily) >= 7 else daily
    ma = sum(window) / len(window)
    std = statistics.pstdev(window) if len(window) > 1 else ma * 0.1

    forecast = []
    for i in range(1, 8):
        day = (now + timedelta(days=i)).date().isoformat()
        forecast.append(
            ForecastItem(
                date=day,
                predicted_count=round(ma, 2),
                lower_bound=round(max(0, ma - std), 2),
                upper_bound=round(ma + std, 2),
            )
        )
    return Dashboard6ForecastResponse(forecast=forecast)


# --- Классические ручки /analytics/* (те же данные, с фильтрами) ---


async def tickets_summary(db: AsyncSession, filters: AnalyticsFilters) -> TicketSummaryResponse:
    ticket_clauses = _ticket_where(filters)
    status_rows = (
        await db.execute(
            select(Ticket.status, func.count())
            .where(*ticket_clauses)
            .group_by(Ticket.status)
        )
    ).all()
    product_rows = (
        await db.execute(
            select(Ticket.product, func.count())
            .where(*ticket_clauses)
            .group_by(Ticket.product)
        )
    ).all()
    category_rows = (
        await db.execute(
            select(Ticket.final_category, func.count())
            .where(*ticket_clauses, Ticket.final_category.is_not(None))
            .group_by(Ticket.final_category)
        )
    ).all()
    return TicketSummaryResponse(
        by_status=[CountItem(key=str(r[0]), count=r[1]) for r in status_rows],
        by_product=[CountItem(key=str(r[0]), count=r[1]) for r in product_rows],
        by_category=[CountItem(key=str(r[0]), count=r[1]) for r in category_rows],
    )


async def tickets_timeline(db: AsyncSession, filters: AnalyticsFilters) -> TicketDynamicsResponse:
    d1 = await dashboard_1(db, filters)
    return TicketDynamicsResponse(
        items=[ExtDateCountItem(date=i.date, count=i.count) for i in d1.dynamics]
    )


async def tickets_sla(db: AsyncSession, filters: AnalyticsFilters) -> SLAStatsResponse:
    tickets = (await db.execute(select(Ticket).where(*_ticket_where(filters)))).scalars().all()
    first_admin = await _first_admin_reply(db, [t.id for t in tickets])
    total = 0
    compliant = 0
    for t in tickets:
        if not t.sla_ttfr_min and not t.sla_ttr_min:
            continue
        total += 1
        ok = True
        admin_at = first_admin.get(t.id)
        if t.sla_ttfr_min and admin_at:
            ok = ok and (admin_at - t.date).total_seconds() / 60 <= t.sla_ttfr_min
        if t.closed_at and t.sla_ttr_min:
            ok = ok and (t.closed_at - t.date).total_seconds() / 60 <= t.sla_ttr_min
        if ok:
            compliant += 1
    breached = max(0, total - compliant)
    rate = (compliant / total * 100) if total else 100.0
    return SLAStatsResponse(
        total=total,
        breached=breached,
        compliant=compliant,
        compliance_rate=round(rate, 2),
    )


async def ai_accuracy(db: AsyncSession, filters: AnalyticsFilters) -> AIAccuracyResponse:
    ticket_clauses = _ticket_where(filters)
    rows = (
        await db.execute(
            select(
                func.count(),
                func.sum(case((Ticket.is_admin_changed.is_(True), 1), else_=0)),
            ).where(*ticket_clauses, Ticket.final_category.is_not(None))
        )
    ).one()
    total, changed = int(rows[0] or 0), int(rows[1] or 0)
    accuracy = ((total - changed) / total * 100) if total else 100.0
    return AIAccuracyResponse(
        total_classified=total,
        admin_changed=changed,
        accuracy_rate=round(accuracy, 2),
    )


async def reviews_summary(db: AsyncSession, filters: AnalyticsFilters) -> ReviewSummaryResponse:
    reviews = (await db.execute(select(Review).where(*_review_where(filters)))).scalars().all()
    total = len(reviews)
    avg = sum(r.rating for r in reviews) / total if total else 0.0
    sentiment: Counter[str] = Counter()
    for r in reviews:
        if r.rating >= 4:
            sentiment["positive"] += 1
        elif r.rating <= 2:
            sentiment["negative"] += 1
        else:
            sentiment["neutral"] += 1
    return ReviewSummaryResponse(
        average_rating=round(avg, 2),
        total_reviews=total,
        sentiment_distribution=[CountItem(key=k, count=v) for k, v in sentiment.items()],
    )


async def reviews_keywords(db: AsyncSession, filters: AnalyticsFilters) -> ReviewKeywordsResponse:
    d5 = await dashboard_5(db, filters)
    return ReviewKeywordsResponse(
        keywords_positive=[CountItem(key=w.word, count=w.count) for w in d5.top_keywords_positive],
        keywords_negative=[CountItem(key=w.word, count=w.count) for w in d5.top_keywords_negative],
    )


async def tickets_reopens(db: AsyncSession, filters: AnalyticsFilters) -> TicketReopensResponse:
    d1 = await dashboard_1(db, filters)
    closed = (
        await db.execute(
            select(func.count()).where(*_ticket_where(filters), Ticket.closed_at.is_not(None))
        )
    ).scalar_one()
    reopened = (
        await db.execute(
            select(func.count()).where(*_ticket_where(filters), Ticket.reopened_count > 0)
        )
    ).scalar_one()
    return TicketReopensResponse(
        total_closed=closed or 0,
        total_reopened=reopened or 0,
        reopen_rate_pct=d1.reopen_rate_pct,
    )


async def ai_efficiency(db: AsyncSession, filters: AnalyticsFilters) -> AIEfficiencyResponse:
    d2 = await dashboard_2(db, filters)
    auto_n = sum(c.count for c in d2.top_ai_resolved_categories)
    esc_n = sum(c.count for c in d2.top_escalated_categories)
    return AIEfficiencyResponse(
        auto_resolved=auto_n,
        escalated=esc_n,
        auto_resolved_pct=d2.current_auto_resolved_pct,
        avg_messages_before_escalation=d2.avg_messages_before_escalation,
        top_escalated_categories=[
            ExtCategoryCountItem(category=c.category, count=c.count)
            for c in d2.top_escalated_categories
        ],
        top_resolved_categories=[
            ExtCategoryCountItem(category=c.category, count=c.count)
            for c in d2.top_ai_resolved_categories
        ],
    )


async def admin_workload(db: AsyncSession, filters: AnalyticsFilters) -> AdminWorkloadResponse:
    d3 = await dashboard_3(db, filters)
    return AdminWorkloadResponse(
        items=[
            AdminWorkloadItem(
                employee_id=w.employee_id,
                username=w.username,
                open_tickets=w.open,
                closed_tickets=w.closed,
            )
            for w in d3.workload
        ]
    )


async def admin_sla(db: AsyncSession, filters: AnalyticsFilters) -> AdminSLAResponse:
    d3 = await dashboard_3(db, filters)
    return AdminSLAResponse(
        by_priority=[
            SLAPriorityItem(
                priority=p.priority,
                avg_ttfr=next((x.avg_min for x in d3.ttfr_by_priority if x.priority == p.priority), 0.0),
                avg_ttr=next((x.avg_min for x in d3.ttr_by_priority if x.priority == p.priority), 0.0),
                sla_ttfr_compliance_pct=p.ttfr_ok_pct,
                sla_ttr_compliance_pct=p.ttr_ok_pct,
            )
            for p in d3.sla_compliance
        ],
        top_violated_categories=[
            ExtCategoryCountItem(category=c.category, count=c.count)
            for c in d3.sla_violations_by_category
        ],
    )


async def admin_heatmap(db: AsyncSession, filters: AnalyticsFilters) -> HeatmapResponse:
    d3 = await dashboard_3(db, filters)
    return HeatmapResponse(
        items=[
            HeatmapItem(day_of_week=h.day_of_week, hour=h.hour, avg_ttfr_min=h.avg_ttfr_min)
            for h in d3.heatmap
        ]
    )


async def users_demographics(db: AsyncSession, filters: AnalyticsFilters) -> UserDemographicsResponse:
    d4 = await dashboard_4(db, filters)
    return UserDemographicsResponse(
        by_gender=[
            DemographicsCountItem(key=g.gender or "не указан", count=g.count) for g in d4.by_gender
        ],
        by_age_group=[
            DemographicsCountItem(key=g.group or "не указан", count=g.count) for g in d4.by_age_group
        ],
        by_city=[DemographicsCountItem(key=g.city or "не указан", count=g.count) for g in d4.by_city],
    )


async def users_retention(db: AsyncSession, filters: AnalyticsFilters) -> UserRetentionResponse:
    d4 = await dashboard_4(db, filters)
    return UserRetentionResponse(
        retention_7d_pct=d4.retention.d7_pct,
        retention_14d_pct=d4.retention.d14_pct,
        retention_30d_pct=d4.retention.d30_pct,
    )


async def reviews_dynamics(db: AsyncSession, filters: AnalyticsFilters) -> ReviewDynamicsResponse:
    d5 = await dashboard_5(db, filters)
    return ReviewDynamicsResponse(
        items=[
            ReviewDynamicsItem(date=i.date, positive_count=i.positive, negative_count=i.negative)
            for i in d5.sentiment_dynamics
        ]
    )


async def tickets_anomalies(db: AsyncSession, filters: AnalyticsFilters) -> TicketAnomaliesResponse:
    d6 = await dashboard_6_tickets(db, filters)
    return TicketAnomaliesResponse(
        items=[
            TicketAnomalyItem(
                category=a.category,
                product=a.product,
                count_48h=a.count_48h,
                rolling_avg=a.rolling_avg,
                stddev=0.0,
                z_score=a.z_score,
            )
            for a in d6.anomalies
        ]
    )


async def tickets_forecast(
    db: AsyncSession,
    *,
    product: str | None,
    category: str | None,
) -> Dashboard6ForecastResponse:
    return await dashboard_6_forecast(db, product=product, category=category)


# Kafka handlers (витрина)
from backend.app.services.analytics_warehouse_service import (  # noqa: E402
    on_ticket_closed,
    on_ticket_created,
)
