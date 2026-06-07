import uuid

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.models.base import Base, TimestampMixin


class SlaRule(Base, TimestampMixin):
    __tablename__ = "sla_rules"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("products.id"), nullable=True, index=True
    )
    priority: Mapped[str] = mapped_column(String(16), nullable=False)
    ttfr_limit_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    ttr_limit_minutes: Mapped[int] = mapped_column(Integer, nullable=False)

    product = relationship("Product", back_populates="sla_rules")
