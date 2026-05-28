import uuid

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.enums import UserRole
from backend.app.models.review import Review
from backend.app.models.ticket import Ticket
from backend.app.schemas.review import ReviewCreate, ReviewUpdate


async def create_review(db: AsyncSession, client_id: uuid.UUID, data: ReviewCreate) -> Review:
    product: str | None = data.product.value if data.product else None
    if data.ticket_id:
        ticket = await db.get(Ticket, data.ticket_id)
        if not ticket:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")
        if ticket.client_id != client_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
        if not product:
            product = ticket.product

    review = Review(
        ticket_id=data.ticket_id,
        client_id=client_id,
        product=product,
        rating=data.rating,
        comment=data.comment,
    )
    db.add(review)
    await db.commit()
    await db.refresh(review)
    return review


async def list_reviews(
    db: AsyncSession,
    user_id: uuid.UUID,
    role: UserRole,
    skip: int,
    limit: int,
    ticket_id: uuid.UUID | None = None,
    product: str | None = None,
) -> list[Review]:
    query = select(Review)
    if role == UserRole.client:
        query = query.where(Review.client_id == user_id)
    if ticket_id:
        query = query.where(Review.ticket_id == ticket_id)
    if product:
        query = query.where(Review.product == product)
    query = query.order_by(Review.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_review(
    db: AsyncSession,
    review_id: uuid.UUID,
    user_id: uuid.UUID,
    role: UserRole,
) -> Review:
    result = await db.execute(select(Review).where(Review.id == review_id))
    review = result.scalar_one_or_none()
    if not review:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review not found")
    if role == UserRole.client and review.client_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    return review


async def update_review(
    db: AsyncSession,
    review_id: uuid.UUID,
    data: ReviewUpdate,
    user_id: uuid.UUID,
    role: UserRole,
) -> Review:
    review = await get_review(db, review_id, user_id, role)
    if role == UserRole.client:
        if data.final_category is not None or data.is_admin_changed is not None:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Clients cannot change classification")
        if data.rating is not None:
            review.rating = data.rating
        if data.comment is not None:
            review.comment = data.comment
        if data.product is not None:
            review.product = data.product.value
    else:
        if data.rating is not None:
            review.rating = data.rating
        if data.comment is not None:
            review.comment = data.comment
        if data.product is not None:
            review.product = data.product.value
        if data.final_category is not None:
            review.final_category = data.final_category
        if data.is_admin_changed is not None:
            review.is_admin_changed = data.is_admin_changed

    await db.commit()
    await db.refresh(review)
    return review
