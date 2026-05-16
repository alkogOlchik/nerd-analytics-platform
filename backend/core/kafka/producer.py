class KafkaProducer:
    """Отправка событий в Kafka."""

    def __init__(self, bootstrap_servers: str) -> None:
        self.bootstrap_servers = bootstrap_servers

    def send(self, topic: str, value: bytes, key: bytes | None = None) -> None:
        pass
