"""Схема аналитической витрины для дашбордов D1–D6."""

from datetime import date

from sqlalchemy import Date, Float, Integer, String, Text
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.analytics_warehouse.base import AnalyticsBase


class General(AnalyticsBase):
    """D1 — обработка тикетов."""

    __tablename__ = "general"

    ticket_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    created_at: Mapped[date | None] = mapped_column(Date, nullable=True)
    closed_at: Mapped[date | None] = mapped_column(Date, nullable=True)
    product: Mapped[str | None] = mapped_column(String(128), nullable=True)
    category: Mapped[str | None] = mapped_column(String(128), nullable=True)
    status: Mapped[str | None] = mapped_column(String(64), nullable=True)
    priority: Mapped[str | None] = mapped_column(String(32), nullable=True)
    admin: Mapped[str | None] = mapped_column(String(255), nullable=True)
    city: Mapped[str | None] = mapped_column(String(128), nullable=True)
    age_group: Mapped[str | None] = mapped_column(String(32), nullable=True)
    ttl_hours: Mapped[float | None] = mapped_column(Float, nullable=True)
    is_reopened: Mapped[int | None] = mapped_column(Integer, nullable=True)
    reopen_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    rating: Mapped[int | None] = mapped_column(Integer, nullable=True)


class AiEffective(AnalyticsBase):
    """D2 — эффективность ИИ."""

    __tablename__ = "ai_effective"

    dialog_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    ticket_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    date: Mapped[date | None] = mapped_column(Date, nullable=True)
    product: Mapped[str | None] = mapped_column(String(128), nullable=True)
    msg_count_before_escalation: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_resolved_by_ai: Mapped[int | None] = mapped_column(Integer, nullable=True)
    escalated_to_human: Mapped[int | None] = mapped_column(Integer, nullable=True)
    ai_response_sec: Mapped[float | None] = mapped_column(Float, nullable=True)
    ai_category_suggested: Mapped[str | None] = mapped_column(String(128), nullable=True)
    admin_changed_category: Mapped[int | None] = mapped_column(Integer, nullable=True)
    final_category: Mapped[str | None] = mapped_column(String(128), nullable=True)
    resolution_time_ai_min: Mapped[float | None] = mapped_column(Float, nullable=True)
    resolution_time_human_min: Mapped[float | None] = mapped_column(Float, nullable=True)


class AdminEffective(AnalyticsBase):
    """D3 — эффективность администратора."""

    __tablename__ = "admin_effective"

    ticket_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    date: Mapped[date | None] = mapped_column(Date, nullable=True)
    hour: Mapped[int | None] = mapped_column(Integer, nullable=True)
    day_of_week: Mapped[str | None] = mapped_column(String(32), nullable=True)
    product: Mapped[str | None] = mapped_column(String(128), nullable=True)
    category: Mapped[str | None] = mapped_column(String(128), nullable=True)
    priority: Mapped[str | None] = mapped_column(String(32), nullable=True)
    admin: Mapped[str | None] = mapped_column(String(255), nullable=True)
    ttfr_min: Mapped[float | None] = mapped_column(Float, nullable=True)
    ttr_min: Mapped[float | None] = mapped_column(Float, nullable=True)
    sla_ttfr_min: Mapped[int | None] = mapped_column(Integer, nullable=True)
    sla_ttr_min: Mapped[int | None] = mapped_column(Integer, nullable=True)
    ttfr_met: Mapped[int | None] = mapped_column(Integer, nullable=True)
    ttr_met: Mapped[int | None] = mapped_column(Integer, nullable=True)
    tickets_closed: Mapped[int | None] = mapped_column(Integer, nullable=True)
    rating_from_user: Mapped[int | None] = mapped_column(Integer, nullable=True)


class FactUsers(AnalyticsBase):
    """D4 — пользователи."""

    __tablename__ = "fact_users"

    user_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    registration_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    gender: Mapped[str | None] = mapped_column(String(16), nullable=True)
    age_group: Mapped[str | None] = mapped_column(String(32), nullable=True)
    city: Mapped[str | None] = mapped_column(String(128), nullable=True)
    product: Mapped[list[str] | None] = mapped_column(ARRAY(String), nullable=True)
    total_tickets: Mapped[int | None] = mapped_column(Integer, nullable=True)
    open_tickets: Mapped[int | None] = mapped_column(Integer, nullable=True)
    closed_tickets: Mapped[int | None] = mapped_column(Integer, nullable=True)
    first_ticket_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    last_ticket_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    retention_7d: Mapped[int | None] = mapped_column(Integer, nullable=True)
    retention_14d: Mapped[int | None] = mapped_column(Integer, nullable=True)
    retention_30d: Mapped[int | None] = mapped_column(Integer, nullable=True)


class FactReviews(AnalyticsBase):
    """D5 — отзывы."""

    __tablename__ = "fact_reviews"

    review_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    ticket_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    date: Mapped[date | None] = mapped_column(Date, nullable=True)
    product: Mapped[str | None] = mapped_column(String(128), nullable=True)
    category: Mapped[str | None] = mapped_column(String(128), nullable=True)
    city: Mapped[str | None] = mapped_column(String(128), nullable=True)
    age_group: Mapped[str | None] = mapped_column(String(32), nullable=True)
    rating: Mapped[int | None] = mapped_column(Integer, nullable=True)
    review_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    sentiment: Mapped[str | None] = mapped_column(String(32), nullable=True)
    keywords_positive: Mapped[str | None] = mapped_column(Text, nullable=True)
    keywords_negative: Mapped[str | None] = mapped_column(Text, nullable=True)


class FactProblems(AnalyticsBase):
    """D6 — проблемы (одна строка на тикет)."""

    __tablename__ = "fact_problems"

    ticket_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    date: Mapped[date | None] = mapped_column(Date, nullable=True)
    hour: Mapped[int | None] = mapped_column(Integer, nullable=True)
    day_of_week: Mapped[str | None] = mapped_column(String(32), nullable=True)
    product: Mapped[str | None] = mapped_column(String(128), nullable=True)
    category: Mapped[str | None] = mapped_column(String(128), nullable=True)
    priority: Mapped[str | None] = mapped_column(String(32), nullable=True)
    city: Mapped[str | None] = mapped_column(String(128), nullable=True)
    age_group: Mapped[str | None] = mapped_column(String(32), nullable=True)
    keywords: Mapped[str | None] = mapped_column(Text, nullable=True)
    ttr_hours: Mapped[float | None] = mapped_column(Float, nullable=True)
    is_anomaly: Mapped[int | None] = mapped_column(Integer, nullable=True)


class FactForecast(AnalyticsBase):
    """D6 — прогноз обращений (time series)."""

    __tablename__ = "fact_forecast"

    forecast_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    forecast_date: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)
    category: Mapped[str | None] = mapped_column(String(128), nullable=True)
    product: Mapped[str | None] = mapped_column(String(128), nullable=True)
    predicted_count: Mapped[float | None] = mapped_column(Float, nullable=True)
