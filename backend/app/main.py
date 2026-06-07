import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.api.v1 import ai, analytics, auth, notifications, reviews, tickets
from backend.app.services import analytics_service, notification_service
from backend.core.kafka.consumer import event_consumer
from backend.core.kafka.producer import event_producer

logger = logging.getLogger(__name__)


def _register_kafka_handlers() -> None:
    event_consumer.register("ticket.created", notification_service.on_ticket_created)
    event_consumer.register("ticket.closed", notification_service.on_ticket_closed)
    event_consumer.register("ticket.breached", notification_service.on_ticket_breached)
    event_consumer.register("ticket.created", analytics_service.on_ticket_created)
    event_consumer.register("ticket.closed", analytics_service.on_ticket_closed)


async def _stop_kafka() -> None:
    try:
        await event_consumer.stop()
    except Exception:
        logger.debug("Kafka consumer stop skipped", exc_info=True)
    try:
        await event_producer.stop()
    except Exception:
        logger.debug("Kafka producer stop skipped", exc_info=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    _register_kafka_handlers()
    try:
        await asyncio.wait_for(event_producer.start(), timeout=5.0)
        await asyncio.wait_for(event_consumer.start(), timeout=5.0)
    except (asyncio.TimeoutError, Exception) as exc:
        logger.warning("Kafka unavailable, running without event bus: %s", exc)
        await _stop_kafka()
    try:
        yield
    finally:
        await _stop_kafka()


app = FastAPI(title="Нёрд-аналитика", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(tickets.router)
app.include_router(reviews.router)
app.include_router(notifications.router)
app.include_router(analytics.router)
app.include_router(ai.router)


@app.get("/health")
async def health():
    return {"status": "ok"}
