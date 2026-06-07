from dataclasses import dataclass
from datetime import datetime

from fastapi import Query

from backend.app.services.analytics_service import AnalyticsFilters, resolve_filters


@dataclass
class AnalyticsQueryParams:
    filters: AnalyticsFilters


def get_analytics_filters(
    date_from: datetime | None = Query(default=None, alias="date_from"),
    date_to: datetime | None = Query(default=None, alias="date_to"),
    product: str | None = Query(default=None),
    priority: str | None = Query(default=None),
    category: str | None = Query(default=None),
) -> AnalyticsQueryParams:
    return AnalyticsQueryParams(
        filters=resolve_filters(
            date_from=date_from,
            date_to=date_to,
            product=product,
            priority=priority,
            category=category,
        )
    )
