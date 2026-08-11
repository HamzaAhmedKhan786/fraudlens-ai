import asyncio
import logging
from datetime import UTC, datetime

from sqlalchemy import delete, select

from fraudlens.database import AuditRecord, UploadRecord, session_factory
from fraudlens.dependencies import get_storage

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("fraudlens.retention")


async def enforce_once() -> tuple[int, int]:
    now = datetime.now(UTC)
    storage = get_storage()
    objects_deleted = 0
    metadata_deleted = 0
    async with session_factory() as session:
        expired_objects = list(
            await session.scalars(
                select(UploadRecord).where(
                    UploadRecord.object_available.is_(True),
                    UploadRecord.retention_expires_at <= now,
                )
            )
        )
        for upload in expired_objects:
            await storage.delete(upload.storage_key)
            upload.object_available = False
            upload.status = "RETAINED_METADATA_ONLY"
            session.add(
                AuditRecord(
                    tenant_id=upload.tenant_id,
                    actor="retention-worker",
                    action="upload.object_expired",
                    resource_id=upload.id,
                    payload={"storage_key": upload.storage_key},
                )
            )
            objects_deleted += 1
        metadata_ids = list(
            await session.scalars(
                select(UploadRecord.id).where(UploadRecord.metadata_expires_at <= now)
            )
        )
        if metadata_ids:
            await session.execute(delete(UploadRecord).where(UploadRecord.id.in_(metadata_ids)))
            metadata_deleted = len(metadata_ids)
        await session.commit()
    return objects_deleted, metadata_deleted


async def run() -> None:
    while True:
        try:
            objects, metadata = await enforce_once()
            logger.info("Retention pass: %s objects, %s metadata rows", objects, metadata)
        except Exception:
            logger.exception("Retention pass failed")
        await asyncio.sleep(86_400)


if __name__ == "__main__":
    asyncio.run(run())
