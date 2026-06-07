"""SLA checker: background job, runs every 5 minutes via APScheduler."""

import logging
import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db.session import AsyncSessionLocal
from backend.app.models.enums import TicketStatus
from backend.app.models.sla_rule import SlaRule
from backend.app.models.ticket import Ticket
from backend.app.models.ticket_status_history import TicketStatusHistory

logger = logging.getLogger(__name__)

_OPEN_STATUSES = {
    TicketStatus.accepted.value,
    TicketStatus.in_progress.value,
    TicketStatus.needs_info.value,
    TicketStatus.dev_handoff.value,
}


async def _load_sla_rules(db: AsyncSession) -> dict[tuple[str | None, str], SlaRule]:
    """Return rules keyed by (product_id_str | None, priority)."""
    result = await db.execute(select(SlaRule))
    rules: dict[tuple[str | None, str], SlaRule] = {}
    for rule in result.scalars().all():
        key = (str(rule.product_id) if rule.product_id else None, rule.priority)
        rules[key] = rule
    return rules


def _pick_rule(
    rules: dict[tuple[str | None, str], SlaRule],
    product_id: uuid.UUID | None,
    priority: str,
) -> SlaRule | None:
    pid = str(product_id) if product_id else None
    return rules.get((pid, priority)) or rules.get((None, priority))


async def check_sla_breaches() -> None:
    """Called by scheduler every 5 minutes. Emits kafka events for breached tickets."""
    now = datetime.now(UTC)
    async with AsyncSessionLocal() as db:
        rules = await _load_sla_rules(db)
        if not rules:
            return

        stmt = select(Ticket).where(Ticket.status.in_(_OPEN_STATUSES))
        result = await db.execute(stmt)
        tickets = result.scalars().all()

        breached: list[Ticket] = []
        for ticket in tickets:
            rule = _pick_rule(rules, ticket.product_id, ticket.admin_priority or ticket.priority)
            if not rule:
                continue

            ticket_date = ticket.date.replace(tzinfo=UTC) if ticket.date.tzinfo is None else ticket.date

            # TTFR breach: no status change away from "принято" within limit
            ttfr_deadline = ticket_date + timedelta(minutes=rule.ttfr_limit_minutes)
            if ticket.status == TicketStatus.accepted.value and now > ttfr_deadline:
                if ticket.sla_ttfr_min is None:
                    ticket.sla_ttfr_min = int((now - ticket_date).total_seconds() / 60)
                    breached.append(ticket)
                    continue

            # TTR breach: total open time exceeds limit
            ttr_deadline = ticket_date + timedelta(minutes=rule.ttr_limit_minutes)
            if now > ttr_deadline and ticket.sla_ttr_min is None:
                ticket.sla_ttr_min = int((now - ticket_date).total_seconds() / 60)
                breached.append(ticket)

        if breached:
            await db.commit()
            for ticket in breached:
                logger.warning("SLA breach ticket=%s status=%s", ticket.id, ticket.status)
                await _emit_breach_event(ticket)


async def _emit_breach_event(ticket: Ticket) -> None:
    try:
        from backend.core.kafka.producer import event_producer

        await event_producer.send(
            "ticket.breached",
            {"ticket_id": str(ticket.id), "client_id": str(ticket.client_id)},
        )
    except Exception as exc:
        logger.debug("Kafka unavailable for breach event: %s", exc)


def start_scheduler():
    """Start APScheduler with SLA check job. Returns scheduler instance."""
    try:
        from apscheduler.schedulers.asyncio import AsyncIOScheduler

        scheduler = AsyncIOScheduler()
        scheduler.add_job(check_sla_breaches, "interval", minutes=5, id="sla_check")
        scheduler.start()
        logger.info("SLA scheduler started")
        return scheduler
    except ImportError:
        logger.warning("APScheduler not installed — SLA background job disabled")
        return None
