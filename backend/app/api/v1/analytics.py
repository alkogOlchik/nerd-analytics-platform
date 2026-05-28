from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.api.deps import CurrentUser, require_analyst
from backend.app.db.analytics_session import get_analytics_db
from backend.app.models.enums import TicketProduct
from backend.app.schemas.analytics import (
    AIAccuracyResponse,
    ReviewKeywordsResponse,
    ReviewSummaryResponse,
    SLAStatsResponse,
    TicketSummaryResponse,
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
from backend.app.services import analytics_warehouse_service as analytics_service

router = APIRouter(prefix="/analytics", tags=["analytics"])


def _product_param(product: TicketProduct | None) -> str | None:
    return product.value if product else None


@router.get("/tickets/summary", response_model=TicketSummaryResponse)
async def tickets_summary(
    db: AsyncSession = Depends(get_analytics_db),
    _: CurrentUser = Depends(require_analyst),
):
    return await analytics_service.tickets_summary(db)


@router.get("/tickets/sla", response_model=SLAStatsResponse)
async def tickets_sla(
    db: AsyncSession = Depends(get_analytics_db),
    _: CurrentUser = Depends(require_analyst),
):
    return await analytics_service.tickets_sla(db)


@router.get("/ai/accuracy", response_model=AIAccuracyResponse)
async def ai_accuracy(
    db: AsyncSession = Depends(get_analytics_db),
    _: CurrentUser = Depends(require_analyst),
):
    return await analytics_service.ai_accuracy(db)


@router.get("/reviews/summary", response_model=ReviewSummaryResponse)
async def reviews_summary(
    db: AsyncSession = Depends(get_analytics_db),
    _: CurrentUser = Depends(require_analyst),
):
    return await analytics_service.reviews_summary(db)


@router.get("/reviews/keywords", response_model=ReviewKeywordsResponse)
async def reviews_keywords(
    db: AsyncSession = Depends(get_analytics_db),
    _: CurrentUser = Depends(require_analyst),
):
    return await analytics_service.reviews_keywords(db)


@router.get("/tickets/dynamics", response_model=TicketDynamicsResponse)
async def tickets_dynamics(
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    product: TicketProduct | None = None,
    db: AsyncSession = Depends(get_analytics_db),
    _: CurrentUser = Depends(require_analyst),
):
    return await analytics_service.tickets_dynamics(
        db, date_from=date_from, date_to=date_to, product=_product_param(product)
    )


@router.get("/tickets/reopens", response_model=TicketReopensResponse)
async def tickets_reopens(
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    product: TicketProduct | None = None,
    db: AsyncSession = Depends(get_analytics_db),
    _: CurrentUser = Depends(require_analyst),
):
    return await analytics_service.tickets_reopens(
        db, date_from=date_from, date_to=date_to, product=_product_param(product)
    )


@router.get("/ai/efficiency", response_model=AIEfficiencyResponse)
async def ai_efficiency(
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    product: TicketProduct | None = None,
    db: AsyncSession = Depends(get_analytics_db),
    _: CurrentUser = Depends(require_analyst),
):
    return await analytics_service.ai_efficiency(
        db, date_from=date_from, date_to=date_to, product=_product_param(product)
    )


@router.get("/admin/workload", response_model=AdminWorkloadResponse)
async def admin_workload(
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    product: TicketProduct | None = None,
    db: AsyncSession = Depends(get_analytics_db),
    _: CurrentUser = Depends(require_analyst),
):
    return await analytics_service.admin_workload(
        db, date_from=date_from, date_to=date_to, product=_product_param(product)
    )


@router.get("/admin/sla", response_model=AdminSLAResponse)
async def admin_sla(
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    product: TicketProduct | None = None,
    db: AsyncSession = Depends(get_analytics_db),
    _: CurrentUser = Depends(require_analyst),
):
    return await analytics_service.admin_sla(
        db, date_from=date_from, date_to=date_to, product=_product_param(product)
    )


@router.get("/admin/heatmap", response_model=HeatmapResponse)
async def admin_heatmap(
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    product: TicketProduct | None = None,
    db: AsyncSession = Depends(get_analytics_db),
    _: CurrentUser = Depends(require_analyst),
):
    return await analytics_service.admin_heatmap(
        db, date_from=date_from, date_to=date_to, product=_product_param(product)
    )


@router.get("/users/demographics", response_model=UserDemographicsResponse)
async def users_demographics(
    product: TicketProduct | None = None,
    db: AsyncSession = Depends(get_analytics_db),
    _: CurrentUser = Depends(require_analyst),
):
    return await analytics_service.users_demographics(db, product=_product_param(product))


@router.get("/users/retention", response_model=UserRetentionResponse)
async def users_retention(
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    product: TicketProduct | None = None,
    db: AsyncSession = Depends(get_analytics_db),
    _: CurrentUser = Depends(require_analyst),
):
    return await analytics_service.users_retention(
        db, date_from=date_from, date_to=date_to, product=_product_param(product)
    )


@router.get("/reviews/dynamics", response_model=ReviewDynamicsResponse)
async def reviews_dynamics(
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    product: TicketProduct | None = None,
    db: AsyncSession = Depends(get_analytics_db),
    _: CurrentUser = Depends(require_analyst),
):
    return await analytics_service.reviews_dynamics(
        db, date_from=date_from, date_to=date_to, product=_product_param(product)
    )


@router.get("/tickets/anomalies", response_model=TicketAnomaliesResponse)
async def tickets_anomalies(
    product: TicketProduct | None = None,
    db: AsyncSession = Depends(get_analytics_db),
    _: CurrentUser = Depends(require_analyst),
):
    return await analytics_service.tickets_anomalies(db, product=_product_param(product))


@router.get("/tickets/forecast")
async def tickets_forecast(
    product: TicketProduct | None = None,
    category: str | None = None,
    db: AsyncSession = Depends(get_analytics_db),
    _: CurrentUser = Depends(require_analyst),
):
    """Прогноз обращений (таблица fact_forecast, модель time_series)."""
    return await analytics_service.tickets_forecast(
        db, product=_product_param(product), category=category
    )
