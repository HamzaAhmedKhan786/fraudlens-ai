import json
from typing import Protocol


class EventPublisher(Protocol):
    async def start(self) -> None: ...
    async def stop(self) -> None: ...
    async def publish(self, key: str, event: dict[str, object]) -> None: ...


class InMemoryEventPublisher:
    def __init__(self) -> None:
        self.events: list[dict[str, object]] = []

    async def start(self) -> None:
        pass

    async def stop(self) -> None:
        pass

    async def publish(self, key: str, event: dict[str, object]) -> None:
        self.events.append({"key": key, **event})


class KafkaEventPublisher:
    def __init__(self, bootstrap_servers: str, topic: str) -> None:
        from aiokafka import AIOKafkaProducer

        self._topic = topic
        self._producer = AIOKafkaProducer(
            bootstrap_servers=bootstrap_servers,
            value_serializer=lambda value: json.dumps(value).encode(),
            key_serializer=lambda value: value.encode(),
            acks="all",
            enable_idempotence=True,
        )

    async def start(self) -> None:
        await self._producer.start()

    async def stop(self) -> None:
        await self._producer.stop()

    async def publish(self, key: str, event: dict[str, object]) -> None:
        await self._producer.send_and_wait(self._topic, value=event, key=key)
