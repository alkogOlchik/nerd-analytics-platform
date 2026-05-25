import json
import logging
from typing import Any

from aiokafka import AIOKafkaProducer

from backend.app.config import get_settings

logger = logging.getLogger(__name__)

TOPIC = "nerd-events"


class KafkaProducer:
    """Отправка событий в Kafka."""

    def __init__(self) -> None:
        self._producer: AIOKafkaProducer | None = None

    async def start(self) -> None:
        settings = get_settings()
        self._producer = AIOKafkaProducer(bootstrap_servers=settings.KAFKA_URL)
        await self._producer.start()
        logger.info("Kafka producer started")

    async def stop(self) -> None:
        if self._producer:
            await self._producer.stop()
            self._producer = None
            logger.info("Kafka producer stopped")

    async def publish(self, event_type: str, payload: dict[str, Any]) -> None:
        if not self._producer:
            logger.warning("Kafka producer not started, skipping event %s", event_type)
            return
        message = json.dumps({"event": event_type, "payload": payload}).encode()
        await self._producer.send_and_wait(TOPIC, message)
        logger.info("Published event %s", event_type)


event_producer = KafkaProducer()
