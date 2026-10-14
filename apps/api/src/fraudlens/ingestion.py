from datetime import UTC, datetime, timedelta
from hashlib import sha256
from uuid import uuid4

from fastapi import HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from fraudlens.auth import Principal
from fraudlens.config import Settings
from fraudlens.database import AuditRecord, EvidenceRecord, UploadRecord
from fraudlens.events import EventPublisher
from fraudlens.file_security import detect_content_type, safe_filename
from fraudlens.orchestrator import InvestigationOrchestrator
from fraudlens.parsers import EvidenceParser
from fraudlens.scanner import VirusScanner
from fraudlens.schemas import UploadList, UploadSummary
from fraudlens.services import get_case, investigate_case
from fraudlens.storage import ObjectStorage


def upload_summary(record: UploadRecord) -> UploadSummary:
    return UploadSummary(
        id=record.id,
        case_id=record.case_id,
        filename=record.filename,
        declared_content_type=record.declared_content_type,
        detected_content_type=record.detected_content_type,
        size_bytes=record.size_bytes,
        sha256=record.sha256,
        status=record.status,
        scan_status=record.scan_status,
        processing_attempts=record.processing_attempts,
        extracted=record.extracted,
        error=record.error,
        object_available=record.object_available,
        retention_expires_at=record.retention_expires_at,
        metadata_expires_at=record.metadata_expires_at,
        created_at=record.created_at,
        updated_at=record.updated_at,
    )


class IngestionService:
    def __init__(
        self,
        settings: Settings,
        storage: ObjectStorage,
        scanner: VirusScanner,
        parser: EvidenceParser,
        publisher: EventPublisher,
        orchestrator: InvestigationOrchestrator,
    ) -> None:
        self.settings = settings
        self.storage = storage
        self.scanner = scanner
        self.parser = parser
        self.publisher = publisher
        self.orchestrator = orchestrator

    async def ingest(
        self,
        session: AsyncSession,
        principal: Principal,
        case_id: str,
        file: UploadFile,
    ) -> UploadSummary:
        await get_case(session, principal, case_id)
        filename = safe_filename(file.filename)
        data = await self._read_limited(file)
        digest = sha256(data).hexdigest()
        existing = await session.scalar(
            select(UploadRecord).where(
                UploadRecord.tenant_id == principal.tenant_id,
                UploadRecord.sha256 == digest,
            )
        )
        if existing:
            return upload_summary(existing)
        try:
            content_type = detect_content_type(data, filename)
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail=str(exc),
            ) from exc

        try:
            scan = await self.scanner.scan(data)
        except RuntimeError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=str(exc),
            ) from exc

        upload_id = str(uuid4())
        quarantined = scan.status == "INFECTED"
        prefix = "quarantine" if quarantined else "accepted"
        storage_key = f"{principal.tenant_id}/{prefix}/{upload_id}/{filename}"
        await self.storage.put(storage_key, data, content_type)
        now = datetime.now(UTC)
        record = UploadRecord(
            id=upload_id,
            case_id=case_id,
            tenant_id=principal.tenant_id,
            filename=filename,
            declared_content_type=file.content_type,
            detected_content_type=content_type,
            size_bytes=len(data),
            sha256=digest,
            storage_bucket=self.storage.bucket,
            storage_key=storage_key,
            status="QUARANTINED" if quarantined else "STORED",
            scan_status=scan.status,
            error=f"Malware detected: {scan.signature}" if quarantined else None,
            object_available=True,
            retention_expires_at=now + timedelta(days=self.settings.upload_retention_days),
            metadata_expires_at=now + timedelta(days=self.settings.metadata_retention_days),
            created_at=now,
            updated_at=now,
        )
        session.add(record)
        session.add(
            AuditRecord(
                tenant_id=principal.tenant_id,
                actor=principal.subject,
                action="upload.quarantined" if quarantined else "upload.accepted",
                resource_id=record.id,
                payload={
                    "case_id": case_id,
                    "filename": filename,
                    "sha256": digest,
                    "size_bytes": len(data),
                },
            )
        )
        await session.commit()
        await self.publisher.publish(
            case_id,
            {
                "type": "evidence.quarantined" if quarantined else "evidence.uploaded",
                "version": 1,
                "upload_id": record.id,
                "case_id": case_id,
                "tenant_id": principal.tenant_id,
            },
        )
        if not quarantined and self.settings.processing_inline:
            await self.process(session, principal, record.id)
        await session.refresh(record)
        return upload_summary(record)

    async def process(
        self,
        session: AsyncSession,
        principal: Principal,
        upload_id: str,
    ) -> UploadSummary:
        record = await self._get_record(session, principal, upload_id)
        if record.status == "QUARANTINED":
            raise HTTPException(status_code=409, detail="Quarantined evidence cannot be processed")
        if record.status == "PROCESSED":
            return upload_summary(record)
        record.status = "PROCESSING"
        record.processing_attempts += 1
        record.error = None
        record.updated_at = datetime.now(UTC)
        await session.commit()
        try:
            data = await self.storage.get(record.storage_key)
            parsed = self.parser.parse(record.detected_content_type, data)
            record.extracted = parsed.attributes
            evidence_id = f"upload-{record.id}"
            if not await session.get(EvidenceRecord, evidence_id):
                session.add(
                    EvidenceRecord(
                        id=evidence_id,
                        case_id=record.case_id,
                        kind=parsed.kind,
                        source=record.filename,
                        attributes=parsed.attributes,
                        sha256=record.sha256,
                    )
                )
            record.status = "PROCESSED"
            record.updated_at = datetime.now(UTC)
            session.add(
                AuditRecord(
                    tenant_id=principal.tenant_id,
                    actor=principal.subject,
                    action="upload.processed",
                    resource_id=record.id,
                    payload={"case_id": record.case_id, "evidence_id": evidence_id},
                )
            )
            await session.commit()
            case_id = record.case_id
            processed_upload_id = record.id
            session.expire_all()
            await investigate_case(
                session,
                principal,
                case_id,
                self.orchestrator,
            )
            await self.publisher.publish(
                case_id,
                {
                    "type": "evidence.processed",
                    "version": 1,
                    "upload_id": processed_upload_id,
                    "case_id": case_id,
                },
            )
        except Exception as exc:
            record = await self._get_record(session, principal, upload_id)
            record.error = str(exc)[:2000]
            record.status = "RETRY_PENDING" if record.processing_attempts < 3 else "DEAD_LETTER"
            record.updated_at = datetime.now(UTC)
            await session.commit()
            await self.publisher.publish(
                record.case_id,
                {
                    "type": "evidence.retry_requested"
                    if record.status == "RETRY_PENDING"
                    else "evidence.dead_lettered",
                    "version": 1,
                    "upload_id": record.id,
                    "case_id": record.case_id,
                    "tenant_id": principal.tenant_id,
                    "attempt": record.processing_attempts,
                    "error": record.error,
                },
            )
        await session.refresh(record)
        return upload_summary(record)

    async def list(
        self, session: AsyncSession, principal: Principal, case_id: str | None = None
    ) -> UploadList:
        statement = select(UploadRecord).where(UploadRecord.tenant_id == principal.tenant_id)
        if case_id:
            statement = statement.where(UploadRecord.case_id == case_id)
        rows = await session.scalars(statement.order_by(UploadRecord.created_at.desc()).limit(200))
        items = [upload_summary(row) for row in rows.all()]
        return UploadList(items=items, total=len(items))

    async def get(
        self, session: AsyncSession, principal: Principal, upload_id: str
    ) -> UploadSummary:
        return upload_summary(await self._get_record(session, principal, upload_id))

    async def download(
        self, session: AsyncSession, principal: Principal, upload_id: str
    ) -> tuple[bytes, UploadRecord]:
        record = await self._get_record(session, principal, upload_id)
        if not record.object_available:
            raise HTTPException(status_code=410, detail="Original evidence has expired")
        if record.status == "QUARANTINED":
            raise HTTPException(status_code=423, detail="Quarantined evidence cannot be downloaded")
        return await self.storage.get(record.storage_key), record

    async def _get_record(
        self, session: AsyncSession, principal: Principal, upload_id: str
    ) -> UploadRecord:
        record = await session.scalar(
            select(UploadRecord).where(
                UploadRecord.id == upload_id,
                UploadRecord.tenant_id == principal.tenant_id,
            )
        )
        if not record:
            raise HTTPException(status_code=404, detail="Upload not found")
        return record

    async def _read_limited(self, file: UploadFile) -> bytes:
        chunks: list[bytes] = []
        size = 0
        while chunk := await file.read(self.settings.upload_chunk_bytes):
            size += len(chunk)
            if size > self.settings.max_upload_bytes:
                raise HTTPException(status_code=413, detail="Upload exceeds the 50 MB limit")
            chunks.append(chunk)
        if not chunks:
            raise HTTPException(status_code=400, detail="Empty files are not accepted")
        return b"".join(chunks)
