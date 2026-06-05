"""ticket_id / dialog_id as UUID (как в nerd_db)

Revision ID: analytics_002
Revises: analytics_001
Create Date: 2026-05-28
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "analytics_002"
down_revision: Union[str, None] = "analytics_001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Витрина пересоздаётся: данные всё равно заливаются ETL заново
    op.execute(
        "DROP TABLE IF EXISTS fact_forecast, fact_problems, fact_reviews, "
        "fact_users, admin_effective, ai_effective, general CASCADE"
    )

    op.create_table(
        "general",
        sa.Column("ticket_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.Date(), nullable=True),
        sa.Column("closed_at", sa.Date(), nullable=True),
        sa.Column("product", sa.String(128), nullable=True),
        sa.Column("category", sa.String(128), nullable=True),
        sa.Column("status", sa.String(64), nullable=True),
        sa.Column("priority", sa.String(32), nullable=True),
        sa.Column("admin", sa.String(255), nullable=True),
        sa.Column("city", sa.String(128), nullable=True),
        sa.Column("age_group", sa.String(32), nullable=True),
        sa.Column("ttl_hours", sa.Float(), nullable=True),
        sa.Column("is_reopened", sa.Integer(), nullable=True),
        sa.Column("reopen_count", sa.Integer(), nullable=True),
        sa.Column("rating", sa.Integer(), nullable=True),
    )
    op.create_table(
        "ai_effective",
        sa.Column("dialog_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("ticket_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("date", sa.Date(), nullable=True),
        sa.Column("product", sa.String(128), nullable=True),
        sa.Column("msg_count_before_escalation", sa.Integer(), nullable=True),
        sa.Column("is_resolved_by_ai", sa.Integer(), nullable=True),
        sa.Column("escalated_to_human", sa.Integer(), nullable=True),
        sa.Column("ai_response_sec", sa.Float(), nullable=True),
        sa.Column("ai_category_suggested", sa.String(128), nullable=True),
        sa.Column("admin_changed_category", sa.Integer(), nullable=True),
        sa.Column("final_category", sa.String(128), nullable=True),
        sa.Column("resolution_time_ai_min", sa.Float(), nullable=True),
        sa.Column("resolution_time_human_min", sa.Float(), nullable=True),
    )
    op.create_index("ix_ai_effective_ticket_id", "ai_effective", ["ticket_id"])

    op.create_table(
        "admin_effective",
        sa.Column("ticket_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("date", sa.Date(), nullable=True),
        sa.Column("hour", sa.Integer(), nullable=True),
        sa.Column("day_of_week", sa.String(32), nullable=True),
        sa.Column("product", sa.String(128), nullable=True),
        sa.Column("category", sa.String(128), nullable=True),
        sa.Column("priority", sa.String(32), nullable=True),
        sa.Column("admin", sa.String(255), nullable=True),
        sa.Column("ttfr_min", sa.Float(), nullable=True),
        sa.Column("ttr_min", sa.Float(), nullable=True),
        sa.Column("sla_ttfr_min", sa.Integer(), nullable=True),
        sa.Column("sla_ttr_min", sa.Integer(), nullable=True),
        sa.Column("ttfr_met", sa.Integer(), nullable=True),
        sa.Column("ttr_met", sa.Integer(), nullable=True),
        sa.Column("tickets_closed", sa.Integer(), nullable=True),
        sa.Column("rating_from_user", sa.Integer(), nullable=True),
    )
    op.create_table(
        "fact_users",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("registration_date", sa.Date(), nullable=True),
        sa.Column("gender", sa.String(16), nullable=True),
        sa.Column("age_group", sa.String(32), nullable=True),
        sa.Column("city", sa.String(128), nullable=True),
        sa.Column("product", postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column("total_tickets", sa.Integer(), nullable=True),
        sa.Column("open_tickets", sa.Integer(), nullable=True),
        sa.Column("closed_tickets", sa.Integer(), nullable=True),
        sa.Column("first_ticket_date", sa.Date(), nullable=True),
        sa.Column("last_ticket_date", sa.Date(), nullable=True),
        sa.Column("retention_7d", sa.Integer(), nullable=True),
        sa.Column("retention_14d", sa.Integer(), nullable=True),
        sa.Column("retention_30d", sa.Integer(), nullable=True),
    )
    op.create_table(
        "fact_reviews",
        sa.Column("review_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("ticket_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("date", sa.Date(), nullable=True),
        sa.Column("product", sa.String(128), nullable=True),
        sa.Column("category", sa.String(128), nullable=True),
        sa.Column("city", sa.String(128), nullable=True),
        sa.Column("age_group", sa.String(32), nullable=True),
        sa.Column("rating", sa.Integer(), nullable=True),
        sa.Column("review_text", sa.Text(), nullable=True),
        sa.Column("sentiment", sa.String(32), nullable=True),
        sa.Column("keywords_positive", sa.Text(), nullable=True),
        sa.Column("keywords_negative", sa.Text(), nullable=True),
    )
    op.create_index("ix_fact_reviews_ticket_id", "fact_reviews", ["ticket_id"])

    op.create_table(
        "fact_problems",
        sa.Column("ticket_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("date", sa.Date(), nullable=True),
        sa.Column("hour", sa.Integer(), nullable=True),
        sa.Column("day_of_week", sa.String(32), nullable=True),
        sa.Column("product", sa.String(128), nullable=True),
        sa.Column("category", sa.String(128), nullable=True),
        sa.Column("priority", sa.String(32), nullable=True),
        sa.Column("city", sa.String(128), nullable=True),
        sa.Column("age_group", sa.String(32), nullable=True),
        sa.Column("keywords", sa.Text(), nullable=True),
        sa.Column("ttr_hours", sa.Float(), nullable=True),
        sa.Column("is_anomaly", sa.Integer(), nullable=True),
    )
    op.create_table(
        "fact_forecast",
        sa.Column("forecast_id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("forecast_date", sa.Date(), nullable=True),
        sa.Column("category", sa.String(128), nullable=True),
        sa.Column("product", sa.String(128), nullable=True),
        sa.Column("predicted_count", sa.Float(), nullable=True),
    )
    op.create_index("ix_fact_forecast_forecast_date", "fact_forecast", ["forecast_date"])


def downgrade() -> None:
    op.execute(
        "DROP TABLE IF EXISTS fact_forecast, fact_problems, fact_reviews, "
        "fact_users, admin_effective, ai_effective, general CASCADE"
    )
    # Вернуть analytics_001: пользователь делает downgrade до base + upgrade 001
