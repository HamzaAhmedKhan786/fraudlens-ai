import asyncio
import json
import logging

from aiokafka import AIOKafkaConsumer

from fraudlens.auth import Principal
from fraudlens.config import get_settings
from fraudlens.database import session_factory
from fraudlens.dependencies import get_ingestion_service, get_publisher

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("fraudlens.worker")


async def run() -> None:
    settings = get_settings()
    if not settings.kafka_enabled:
        raise RuntimeError("KAFKA_ENABLED must be true for the evidence worker")
    publisher = get_publisher()
    await publisher.start()
    consumer = AIOKafkaConsumer(
        settings.kafka_topic,
        bootstrap_servers=settings.kafka_bootstrap_servers,
        group_id=settings.kafka_consumer_group,
        enable_auto_commit=False,
        auto_offset_reset="earliest",
        value_deserializer=lambda value: json.loads(value.decode()),
    )
    await consumer.start()
    try:
        async for message in consumer:
            event = message.value
            if event.get("type") not in {"evidence.uploaded", "evidence.retry_requested"}:
                await consumer.commit()
                continue
            principal = Principal(
                subject="evidence-worker",
                tenant_id=str(event["tenant_id"]),
                roles=frozenset({"service"}),
            )
            try:
                async with session_factory() as session:
                    result = await get_ingestion_service().process(
                        session,
                        principal,
                        str(event["upload_id"]),
                    )
                logger.info("Processed upload %s with status %s", result.id, result.status)
                await consumer.commit()
            except Exception:
                logger.exception("Evidence worker failed for upload %s", event.get("upload_id"))
                # Do not commit: Kafka redelivers the event. The service itself caps processing
                # attempts and emits evidence.dead_lettered after the third failed attempt.
                await asyncio.sleep(2)
    finally:
        await consumer.stop()
        await publisher.stop()


if __name__ == "__main__":
    asyncio.run(run())
