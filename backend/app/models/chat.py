import uuid

from sqlalchemy import Boolean, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.models.base import Base, TimestampMixin


class ChatHistory(Base, TimestampMixin):
    __tablename__ = "chat_history"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    chat_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    ticket_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tickets.id"), nullable=True, index=True
    )
    client_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("clients.id"), nullable=False, index=True
    )
    role: Mapped[str] = mapped_column(String(16), nullable=False)
    product: Mapped[str | None] = mapped_column(String(64), nullable=True)
    category: Mapped[str | None] = mapped_column(String(64), nullable=True)
    resolved_by_ai: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)

    client = relationship("Client", back_populates="chat_messages")
    ticket = relationship("Ticket", back_populates="chat_messages")
    attachments = relationship(
        "ChatAttachment",
        back_populates="chat_message",
        lazy="selectin",
        cascade="all, delete-orphan",
    )
