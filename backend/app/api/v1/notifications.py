import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.api.deps import CurrentUser, get_current_user
from backend.app.db.session import get_db
from backend.app.schemas.notification import (
    NotificationReadAllResponse,
    NotificationResponse,
    NotificationUpdate,
)
from backend.app.services import notification_service

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("", response_model=list[NotificationResponse])
async def list_notifications(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    return await notification_service.list_notifications(
        db, current_user.id, current_user.role, skip=skip, limit=limit
    )


@router.post("/read-all", response_model=NotificationReadAllResponse)
async def read_all_notifications(
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    updated = await notification_service.mark_all_read(db, current_user.id, current_user.role)
    return NotificationReadAllResponse(updated=updated)


@router.get("/{notification_id}", response_model=NotificationResponse)
async def get_notification(
    notification_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    return await notification_service.get_notification(
        db, notification_id, current_user.id, current_user.role
    )


@router.patch("/{notification_id}", response_model=NotificationResponse)
async def update_notification(
    notification_id: uuid.UUID,
    data: NotificationUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    return await notification_service.update_notification(
        db,
        notification_id,
        current_user.id,
        current_user.role,
        is_read=data.is_read,
    )
