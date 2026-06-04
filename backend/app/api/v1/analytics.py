"""Аналитика: операционная БД (nerd_db) + опционально витрина (nerd_analytics_db)."""

from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.api.analytics_deps import AnalyticsQueryParams, get_analytics_filters
from backend.app.api.deps import CurrentUser, require_employee
from backend.app.db.analytics_session import get_analytics_db
from backend.app.db.session import get_db
from backend.app.models.enums import TicketProduct
from backend.app.schemas.analytics import (
    AIAccuracyResponse,
    ReviewKeywordsResponse,
    ReviewSummaryResponse,
    SLAStatsResponse,
    TicketSummaryResponse,
)
from backend.app.schemas.analytics_dashboards import (
    Dashboard1Response,
    Dashboard2Response,
    Dashboard3Response,
    Dashboard4Response,
    Dashboard5Response,
    Dashboard6ForecastResponse,
    Dashboard6TicketsResponse,
)
from backend.app.schemas.analytics_extended import (
    AdminSLAResponse,
    AdminWorkloadResponse,
    AIEfficiencyResponse,
    HeatmapResponse,
    ReviewDynamicsResponse,
    TicketAnomaliesResponse,
    TicketDynamicsResponse,
    TicketReopensResponse,
    UserDemographicsResponse,
    UserRetentionResponse,
)
from backend.app.services import analytics_service as analytics
from backend.app.services import analytics_warehouse_service as warehouse

router = APIRouter(prefix="/analytics", tags=["analytics"])


def _product_param(product: TicketProduct | None) -> str | None:
    return product.value if product else None


# --- Операционная аналитика (nerd_db), фильтры date_from/date_to/from/to/product/priority/category ---


@router.get("/tickets/summary", response_model=TicketSummaryResponse)
async def tickets_summary(
    q: AnalyticsQueryParams = Depends(get_analytics_filters),
    db: AsyncSession = Depends(get_db),
    _: CurrentUser = Depends(require_employee),
):
    return await analytics.tickets_summary(db, q.filters)


@router.get("/tickets/timeline", response_model=TicketDynamicsResponse)
async def tickets_timeline(
    q: AnalyticsQueryParams = Depends(get_analytics_filters),
    db: AsyncSession = Depends(get_db),
    _: CurrentUser = Depends(require_employee),
):
    """Динамика обращений по дням: [{ date, count }]."""
    return await analytics.tickets_timeline(db, q.filters)


@router.get("/tickets/sla", response_model=SLAStatsResponse)
async def tickets_sla(
    q: AnalyticsQueryParams = Depends(get_analytics_filters),
    db: AsyncSession = Depends(get_db),
    _: CurrentUser = Depends(require_employee),
):
    return await analytics.tickets_sla(db, q.filters)


@router.get("/ai/accuracy", response_model=AIAccuracyResponse)
async def ai_accuracy(
    q: AnalyticsQueryParams = Depends(get_analytics_filters),
    db: AsyncSession = Depends(get_db),
    _: CurrentUser = Depends(require_employee),
):
    return await analytics.ai_accuracy(db, q.filters)


@router.get("/reviews/summary", response_model=ReviewSummaryResponse)
async def reviews_summary(
    q: AnalyticsQueryParams = Depends(get_analytics_filters),
    db: AsyncSession = Depends(get_db),
    _: CurrentUser = Depends(require_employee),
):
    return await analytics.reviews_summary(db, q.filters)


@router.get("/reviews/keywords", response_model=ReviewKeywordsResponse)
async def reviews_keywords(
    q: AnalyticsQueryParams = Depends(get_analytics_filters),
    db: AsyncSession = Depends(get_db),
    _: CurrentUser = Depends(require_employee),
):
    return await analytics.reviews_keywords(db, q.filters)


@router.get("/tickets/dynamics", response_model=TicketDynamicsResponse)
async def tickets_dynamics(
    q: AnalyticsQueryParams = Depends(get_analytics_filters),
    db: AsyncSession = Depends(get_db),
    _: CurrentUser = Depends(require_employee),
):
    """Алиас timeline."""
    return await analytics.tickets_timeline(db, q.filters)


@router.get("/tickets/reopens", response_model=TicketReopensResponse)
async def tickets_reopens(
    q: AnalyticsQueryParams = Depends(get_analytics_filters),
    db: AsyncSession = Depends(get_db),
    _: CurrentUser = Depends(require_employee),
):
    return await analytics.tickets_reopens(db, q.filters)


@router.get("/ai/efficiency", response_model=AIEfficiencyResponse)
async def ai_efficiency(
    q: AnalyticsQueryParams = Depends(get_analytics_filters),
    db: AsyncSession = Depends(get_db),
    _: CurrentUser = Depends(require_employee),
):
    return await analytics.ai_efficiency(db, q.filters)


@router.get("/admin/workload", response_model=AdminWorkloadResponse)
async def admin_workload(
    q: AnalyticsQueryParams = Depends(get_analytics_filters),
    db: AsyncSession = Depends(get_db),
    _: CurrentUser = Depends(require_employee),
):
    return await analytics.admin_workload(db, q.filters)


@router.get("/admin/sla", response_model=AdminSLAResponse)
async def admin_sla(
    q: AnalyticsQueryParams = Depends(get_analytics_filters),
    db: AsyncSession = Depends(get_db),
    _: CurrentUser = Depends(require_employee),
):
    return await analytics.admin_sla(db, q.filters)


@router.get("/admin/heatmap", response_model=HeatmapResponse)
async def admin_heatmap(
    q: AnalyticsQueryParams = Depends(get_analytics_filters),
    db: AsyncSession = Depends(get_db),
    _: CurrentUser = Depends(require_employee),
):
    return await analytics.admin_heatmap(db, q.filters)


@router.get("/users/demographics", response_model=UserDemographicsResponse)
async def users_demographics(
    q: AnalyticsQueryParams = Depends(get_analytics_filters),
    db: AsyncSession = Depends(get_db),
    _: CurrentUser = Depends(require_employee),
):
    return await analytics.users_demographics(db, q.filters)


@router.get("/users/retention", response_model=UserRetentionResponse)
async def users_retention(
    q: AnalyticsQueryParams = Depends(get_analytics_filters),
    db: AsyncSession = Depends(get_db),
    _: CurrentUser = Depends(require_employee),
):
    return await analytics.users_retention(db, q.filters)


@router.get("/reviews/dynamics", response_model=ReviewDynamicsResponse)
async def reviews_dynamics(
    q: AnalyticsQueryParams = Depends(get_analytics_filters),
    db: AsyncSession = Depends(get_db),
    _: CurrentUser = Depends(require_employee),
):
    return await analytics.reviews_dynamics(db, q.filters)


@router.get("/tickets/anomalies", response_model=TicketAnomaliesResponse)
async def tickets_anomalies(
    q: AnalyticsQueryParams = Depends(get_analytics_filters),
    db: AsyncSession = Depends(get_db),
    _: CurrentUser = Depends(require_employee),
):
    return await analytics.tickets_anomalies(db, q.filters)


@router.get("/tickets/forecast", response_model=Dashboard6ForecastResponse)
async def tickets_forecast(
    product: TicketProduct | None = None,
    category: str | None = None,
    db: AsyncSession = Depends(get_db),
    _: CurrentUser = Depends(require_employee),
):
    """Прогноз на 7 дней (скользящее среднее по последним 30 дням)."""
    return await analytics.tickets_forecast(
        db,
        product=_product_param(product),
        category=category,
    )


# --- Агрегированные дашборды (один запрос на экран) ---


@router.get("/dashboard/1", response_model=Dashboard1Response)
async def dashboard_1(
    q: AnalyticsQueryParams = Depends(get_analytics_filters),
    db: AsyncSession = Depends(get_db),
    _: CurrentUser = Depends(require_employee),
):
    return await analytics.dashboard_1(db, q.filters)


@router.get("/dashboard/2", response_model=Dashboard2Response)
async def dashboard_2(
    q: AnalyticsQueryParams = Depends(get_analytics_filters),
    db: AsyncSession = Depends(get_db),
    _: CurrentUser = Depends(require_employee),
):
    return await analytics.dashboard_2(db, q.filters)


@router.get("/dashboard/3", response_model=Dashboard3Response)
async def dashboard_3(
    q: AnalyticsQueryParams = Depends(get_analytics_filters),
    db: AsyncSession = Depends(get_db),
    _: CurrentUser = Depends(require_employee),
):
    return await analytics.dashboard_3(db, q.filters)


@router.get("/dashboard/4", response_model=Dashboard4Response)
async def dashboard_4(
    q: AnalyticsQueryParams = Depends(get_analytics_filters),
    db: AsyncSession = Depends(get_db),
    _: CurrentUser = Depends(require_employee),
):
    return await analytics.dashboard_4(db, q.filters)


@router.get("/dashboard/5", response_model=Dashboard5Response)
async def dashboard_5(
    q: AnalyticsQueryParams = Depends(get_analytics_filters),
    db: AsyncSession = Depends(get_db),
    _: CurrentUser = Depends(require_employee),
):
    return await analytics.dashboard_5(db, q.filters)


@router.get("/dashboard/6/tickets", response_model=Dashboard6TicketsResponse)
async def dashboard_6_tickets(
    q: AnalyticsQueryParams = Depends(get_analytics_filters),
    db: AsyncSession = Depends(get_db),
    _: CurrentUser = Depends(require_employee),
):
    return await analytics.dashboard_6_tickets(db, q.filters)


@router.get("/dashboard/6/forecast", response_model=Dashboard6ForecastResponse)
async def dashboard_6_forecast(
    product: TicketProduct | None = None,
    category: str | None = None,
    db: AsyncSession = Depends(get_db),
    _: CurrentUser = Depends(require_employee),
):
    return await analytics.dashboard_6_forecast(
        db,
        product=_product_param(product),
        category=category,
    )


# --- Витрина nerd_analytics_db (после ETL, без фильтров периода на базовых ручках) ---


@router.get("/warehouse/tickets/summary", response_model=TicketSummaryResponse)
async def warehouse_tickets_summary(
    db: AsyncSession = Depends(get_analytics_db),
    _: CurrentUser = Depends(require_employee),
):
    return await warehouse.tickets_summary(db)


@router.get("/warehouse/tickets/sla", response_model=SLAStatsResponse)
async def warehouse_tickets_sla(
    db: AsyncSession = Depends(get_analytics_db),
    _: CurrentUser = Depends(require_employee),
):
    return await warehouse.tickets_sla(db)


@router.get("/warehouse/ai/accuracy", response_model=AIAccuracyResponse)
async def warehouse_ai_accuracy(
    db: AsyncSession = Depends(get_analytics_db),
    _: CurrentUser = Depends(require_employee),
):
    return await warehouse.ai_accuracy(db)


@router.get("/warehouse/reviews/summary", response_model=ReviewSummaryResponse)
async def warehouse_reviews_summary(
    db: AsyncSession = Depends(get_analytics_db),
    _: CurrentUser = Depends(require_employee),
):
    return await warehouse.reviews_summary(db)


@router.get("/warehouse/reviews/keywords", response_model=ReviewKeywordsResponse)
async def warehouse_reviews_keywords(
    db: AsyncSession = Depends(get_analytics_db),
    _: CurrentUser = Depends(require_employee),
):
    return await warehouse.reviews_keywords(db)
