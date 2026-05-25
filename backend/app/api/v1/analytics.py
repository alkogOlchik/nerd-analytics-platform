from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.api.deps import CurrentUser, get_current_user, require_employee
from backend.app.db.session import get_db
from backend.app.schemas.analytics import (
    AIAccuracyResponse,
    ReviewKeywordsResponse,
    ReviewSummaryResponse,
    SLAStatsResponse,
    TicketSummaryResponse,
)
from backend.app.services import analytics_service

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/tickets/summary", response_model=TicketSummaryResponse)
async def tickets_summary(
    db: AsyncSession = Depends(get_db),
    _: CurrentUser = Depends(require_employee),
):
    return await analytics_service.tickets_summary(db)


@router.get("/tickets/sla", response_model=SLAStatsResponse)
async def tickets_sla(
    db: AsyncSession = Depends(get_db),
    _: CurrentUser = Depends(require_employee),
):
    return await analytics_service.tickets_sla(db)


@router.get("/ai/accuracy", response_model=AIAccuracyResponse)
async def ai_accuracy(
    db: AsyncSession = Depends(get_db),
    _: CurrentUser = Depends(require_employee),
):
    return await analytics_service.ai_accuracy(db)


@router.get("/reviews/summary", response_model=ReviewSummaryResponse)
async def reviews_summary(
    db: AsyncSession = Depends(get_db),
    _: CurrentUser = Depends(require_employee),
):
    return await analytics_service.reviews_summary(db)


@router.get("/reviews/keywords", response_model=ReviewKeywordsResponse)
async def reviews_keywords(
    db: AsyncSession = Depends(get_db),
    _: CurrentUser = Depends(require_employee),
):
    return await analytics_service.reviews_keywords(db)
