import asyncio
import json
import logging
from collections.abc import Awaitable, Callable

from aiokafka import AIOKafkaConsumer

from backend.app.config import get_settings
from backend.core.kafka.producer import TOPIC

logger = logging.getLogger(__name__)

EventHandler = Callable[[dict], Awaitable[None]]


class KafkaConsumer:
    """Подписка на события Kafka."""

    def __init__(self) -> None:
        self._consumer: AIOKafkaConsumer | None = None
        self._task: asyncio.Task | None = None
        self._handlers: dict[str, list[EventHandler]] = {}

    def register(self, event_type: str, handler: EventHandler) -> None:
        self._handlers.setdefault(event_type, []).append(handler)

    async def start(self) -> None:
        settings = get_settings()
        self._consumer = AIOKafkaConsumer(
            TOPIC,
            bootstrap_servers=settings.KAFKA_URL,
            group_id="nerd-analytics",
            auto_offset_reset="earliest",
        )
        await self._consumer.start()
        self._task = asyncio.create_task(self._consume_loop())
        logger.info("Kafka consumer started")

    async def stop(self) -> None:
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        if self._consumer:
            await self._consumer.stop()
            self._consumer = None
        logger.info("Kafka consumer stopped")

    async def _consume_loop(self) -> None:
        assert self._consumer is not None
        try:
            async for msg in self._consumer:
                try:
                    data = json.loads(msg.value.decode())
                    event_type = data.get("event")
                    payload = data.get("payload", {})
                    if event_type and event_type in self._handlers:
                        for handler in self._handlers[event_type]:
                            await handler(payload)
                except Exception:
                    logger.exception("Error processing Kafka message")
        except asyncio.CancelledError:
            raise


event_consumer = KafkaConsumer()
