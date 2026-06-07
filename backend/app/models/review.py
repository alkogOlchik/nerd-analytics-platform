import uuid

from sqlalchemy import Boolean, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.models.base import Base, TimestampMixin


class Review(Base, TimestampMixin):
    __tablename__ = "reviews"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ticket_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tickets.id"), nullable=True, index=True
    )
    client_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("clients.id"), nullable=False, index=True
    )
    product: Mapped[str | None] = mapped_column(String(64), nullable=True)
    rating: Mapped[int] = mapped_column(Integer, nullable=False)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    ai_suggested_category: Mapped[str | None] = mapped_column(String(64), nullable=True)
    final_category: Mapped[str | None] = mapped_column(String(64), nullable=True)
    is_admin_changed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    sentiment: Mapped[str | None] = mapped_column(String(16), nullable=True)
    keywords_positive: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    keywords_neutral: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    keywords_negative: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)

    ticket = relationship("Ticket", back_populates="reviews")
    client = relationship("Client", back_populates="reviews")
