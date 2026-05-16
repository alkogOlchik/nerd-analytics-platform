from collections.abc import Callable


class KafkaConsumer:
    """Подписка на события Kafka."""

    def __init__(self, bootstrap_servers: str, group_id: str) -> None:
        self.bootstrap_servers = bootstrap_servers
        self.group_id = group_id

    def subscribe(self, topics: list[str], handler: Callable[[bytes], None]) -> None:
        pass
