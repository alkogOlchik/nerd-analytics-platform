import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.models.base import Base, TimestampMixin


class Ticket(Base):
    __tablename__ = "tickets"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    client_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("clients.id"), nullable=False, index=True
    )
    responsible_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("employees.id"), nullable=True, index=True
    )
    product: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="open")
    priority: Mapped[str] = mapped_column(String(16), nullable=False, default="medium")
    date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    deadline: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    reopened_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_reopened_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    ai_suggested_category: Mapped[str | None] = mapped_column(String(64), nullable=True)
    final_category: Mapped[str | None] = mapped_column(String(64), nullable=True)
    is_admin_changed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    keywords: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    sla_ttfr_min: Mapped[int | None] = mapped_column(Integer, nullable=True)
    sla_ttr_min: Mapped[int | None] = mapped_column(Integer, nullable=True)

    client = relationship("Client", back_populates="tickets")
    responsible = relationship("Employee", back_populates="assigned_tickets")
    attachments = relationship("Attachment", back_populates="ticket", lazy="selectin")
    notifications = relationship("Notification", back_populates="ticket", lazy="selectin")
    reviews = relationship("Review", back_populates="ticket", lazy="selectin")
    chat_messages = relationship("ChatHistory", back_populates="ticket", lazy="selectin")


class Attachment(Base, TimestampMixin):
    __tablename__ = "attachments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ticket_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tickets.id"), nullable=False, index=True
    )
    file_url: Mapped[str] = mapped_column(String(1024), nullable=False)
    file_type: Mapped[str | None] = mapped_column(String(64), nullable=True)

    ticket = relationship("Ticket", back_populates="attachments")
