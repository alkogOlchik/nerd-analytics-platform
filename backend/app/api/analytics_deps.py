"""Общие query-параметры для /analytics (операционная БД)."""

from dataclasses import dataclass
from datetime import datetime

from fastapi import Query

from backend.app.models.enums import TicketProduct
from backend.app.services.analytics_service import AnalyticsFilters, resolve_filters


@dataclass(frozen=True)
class AnalyticsQueryParams:
    filters: AnalyticsFilters


def get_analytics_filters(
    date_from: datetime | None = Query(
        None,
        description="Начало периода (ISO datetime)",
    ),
    date_to: datetime | None = Query(
        None,
        description="Конец периода (ISO datetime)",
    ),
    from_: datetime | None = Query(
        None,
        alias="from",
        description="Алиас date_from",
    ),
    to: datetime | None = Query(
        None,
        alias="to",
        description="Алиас date_to",
    ),
    product: TicketProduct | None = Query(None),
    priority: str | None = Query(None, description="low | medium | high"),
    category: str | None = Query(None, description="Категория тикета/отзыва"),
) -> AnalyticsQueryParams:
    product_value = product.value if product else None
    filters = resolve_filters(
        date_from=from_ or date_from,
        date_to=to or date_to,
        product=product_value,
        priority=priority,
        category=category,
    )
    return AnalyticsQueryParams(filters=filters)
