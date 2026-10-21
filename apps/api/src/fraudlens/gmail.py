import asyncio
import base64
from datetime import UTC, datetime, timedelta
from email import policy
from email.parser import BytesParser
from hashlib import sha256
from io import BytesIO
from secrets import token_urlsafe
from urllib.parse import urlencode

import httpx
from cryptography.fernet import Fernet, InvalidToken
from fastapi import HTTPException, UploadFile
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.datastructures import Headers

from fraudlens.auth import Principal
from fraudlens.config import Settings
from fraudlens.database import (
    AuditRecord,
    GmailConnectionRecord,
    GmailOAuthStateRecord,
)
from fraudlens.file_security import ALLOWED_TYPES
from fraudlens.ingestion import IngestionService
from fraudlens.schemas import GmailConnection, GmailSyncRequest, GmailSyncResult

AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_URL = "https://oauth2.googleapis.com/token"
REVOKE_URL = "https://oauth2.googleapis.com/revoke"
GMAIL_API = "https://gmail.googleapis.com/gmail/v1/users/me"


class GmailConnector:
    def __init__(self, settings: Settings, ingestion: IngestionService) -> None:
        self.settings = settings
        self.ingestion = ingestion
        configured_key = settings.google_token_encryption_key
        key = (
            configured_key.encode()
            if configured_key
            else base64.urlsafe_b64encode(sha256(settings.api_key.encode()).digest())
        )
        self.cipher = Fernet(key)

    def _require_configured(self) -> None:
        if not self.settings.google_client_id or not self.settings.google_client_secret:
            raise HTTPException(status_code=503, detail="Gmail OAuth is not configured")

    async def authorization_url(self, session: AsyncSession, principal: Principal) -> str:
        self._require_configured()
        await session.execute(
            delete(GmailOAuthStateRecord).where(
                GmailOAuthStateRecord.expires_at < datetime.now(UTC)
            )
        )
        raw_state = token_urlsafe(32)
        session.add(
            GmailOAuthStateRecord(
                state_hash=sha256(raw_state.encode()).hexdigest(),
                tenant_id=principal.tenant_id,
                actor=principal.subject,
                expires_at=datetime.now(UTC)
                + timedelta(seconds=self.settings.oauth_state_ttl_seconds),
            )
        )
        await session.commit()
        query = urlencode(
            {
                "client_id": self.settings.google_client_id,
                "redirect_uri": self.settings.google_redirect_uri,
                "response_type": "code",
                "scope": " ".join(self.settings.gmail_scopes),
                "access_type": "offline",
                "prompt": "consent",
                "include_granted_scopes": "true",
                "state": raw_state,
            }
        )
        return f"{AUTH_URL}?{query}"

    async def callback(self, session: AsyncSession, state: str, code: str) -> str:
        self._require_configured()
        now = datetime.now(UTC)
        consumed = await session.execute(
            delete(GmailOAuthStateRecord)
            .where(
                GmailOAuthStateRecord.state_hash == sha256(state.encode()).hexdigest(),
                GmailOAuthStateRecord.expires_at > now,
            )
            .returning(GmailOAuthStateRecord)
        )
        state_record = consumed.scalar_one_or_none()
        if not state_record:
            await session.rollback()
            raise HTTPException(status_code=400, detail="Invalid or expired OAuth state")
        # Deleting and returning the row is a single database statement. Only one
        # worker can consume a state, and the commit makes replay rejection durable.
        await session.commit()
        token = await self._request_json(
            "POST",
            TOKEN_URL,
            data={
                "code": code,
                "client_id": self.settings.google_client_id,
                "client_secret": self.settings.google_client_secret,
                "redirect_uri": self.settings.google_redirect_uri,
                "grant_type": "authorization_code",
            },
        )
        refresh_token = token.get("refresh_token")
        access_token = token.get("access_token")
        if not refresh_token or not access_token:
            raise HTTPException(status_code=400, detail="Google did not return offline access")
        profile = await self._request_json(
            "GET", f"{GMAIL_API}/profile", headers={"Authorization": f"Bearer {access_token}"}
        )
        connection = await session.scalar(
            select(GmailConnectionRecord).where(
                GmailConnectionRecord.tenant_id == state_record.tenant_id
            )
        )
        if not connection:
            connection = GmailConnectionRecord(
                tenant_id=state_record.tenant_id,
                email_address=str(profile.get("emailAddress", "")),
                encrypted_refresh_token="",
                scopes=[],
                connected_at=now,
            )
            session.add(connection)
        connection.email_address = str(profile.get("emailAddress", ""))
        connection.encrypted_refresh_token = self.cipher.encrypt(refresh_token.encode()).decode()
        connection.scopes = str(token.get("scope", "")).split() or self.settings.gmail_scopes
        connection.status = "CONNECTED"
        connection.last_error = None
        connection.connected_at = now
        session.add(
            AuditRecord(
                tenant_id=state_record.tenant_id,
                actor=state_record.actor,
                action="gmail.connected",
                resource_id=connection.email_address,
                payload={"scopes": connection.scopes},
            )
        )
        await session.commit()
        return self.settings.allowed_origins[0].rstrip("/") + "/connectors?gmail=connected"

    async def status(self, session: AsyncSession, principal: Principal) -> GmailConnection:
        connection = await self._connection(session, principal, required=False)
        if not connection:
            return GmailConnection(connected=False, status="NOT_CONNECTED")
        return GmailConnection(
            connected=connection.status == "CONNECTED",
            email_address=connection.email_address,
            status=connection.status,
            scopes=connection.scopes,
            connected_at=connection.connected_at,
            last_sync_at=connection.last_sync_at,
            last_error=connection.last_error,
        )

    async def disconnect(self, session: AsyncSession, principal: Principal) -> None:
        connection = await self._connection(session, principal, required=False)
        if not connection:
            return
        try:
            token = self._decrypt(connection.encrypted_refresh_token)
            await self._request_json("POST", REVOKE_URL, data={"token": token}, allow_empty=True)
        except HTTPException:
            pass
        await session.delete(connection)
        session.add(
            AuditRecord(
                tenant_id=principal.tenant_id,
                actor=principal.subject,
                action="gmail.disconnected",
                resource_id=connection.email_address,
                payload={},
            )
        )
        await session.commit()

    async def sync(
        self, session: AsyncSession, principal: Principal, request: GmailSyncRequest
    ) -> GmailSyncResult:
        # Validate once before calling Gmail so a mistyped case does not turn every
        # matching message into an identical ingestion failure.
        await self.ingestion.list(session, principal, request.case_id)
        connection = await self._connection(session, principal)
        access_token = await self._refresh_access_token(session, connection)
        query: list[str] = []
        if request.sender:
            query.append(f"from:{request.sender}")
        if request.after:
            query.append(f"after:{request.after}")
        if request.before:
            query.append(f"before:{request.before}")
        if request.has_attachment is not None:
            query.append("has:attachment" if request.has_attachment else "-has:attachment")
        headers = {"Authorization": f"Bearer {access_token}"}
        label_ids = await self._resolve_label_ids(request.label_ids, headers)
        params: list[tuple[str, str | int]] = [
            ("maxResults", request.max_messages),
            ("q", " ".join(query)),
        ]
        params.extend(("labelIds", label) for label in label_ids)
        if request.page_token:
            params.append(("pageToken", request.page_token))
        listing = await self._request_json(
            "GET", f"{GMAIL_API}/messages", headers=headers, params=params
        )
        imported = attachments = duplicates = 0
        failures: list[dict[str, str]] = []
        for item in listing.get("messages", []):
            message_id = str(item.get("id", ""))
            try:
                payload = await self._request_json(
                    "GET",
                    f"{GMAIL_API}/messages/{message_id}",
                    headers=headers,
                    params={"format": "raw"},
                )
                raw = self._decode_base64url(str(payload["raw"]))
                before_count = (
                    await self.ingestion.list(session, principal, request.case_id)
                ).total
                summary = await self.ingestion.ingest(
                    session,
                    principal,
                    request.case_id,
                    UploadFile(
                        file=BytesIO(raw),
                        filename=f"gmail-{message_id}.eml",
                        headers=Headers({"content-type": "message/rfc822"}),
                    ),
                )
                after_count = (await self.ingestion.list(session, principal, request.case_id)).total
                if after_count == before_count:
                    duplicates += 1
                else:
                    imported += 1
                attachments += await self._ingest_attachments(
                    session, principal, request.case_id, raw, message_id
                )
                if summary.status in {"DEAD_LETTER", "QUARANTINED"}:
                    failures.append(
                        {"message_id": message_id, "error": summary.error or summary.status}
                    )
            except Exception as exc:
                failures.append({"message_id": message_id, "error": str(exc)[:300]})
        connection.last_sync_at = datetime.now(UTC)
        connection.last_error = None if not failures else f"{len(failures)} message(s) failed"
        session.add(
            AuditRecord(
                tenant_id=principal.tenant_id,
                actor=principal.subject,
                action="gmail.synced",
                resource_id=connection.email_address,
                payload={
                    "case_id": request.case_id,
                    "imported_messages": imported,
                    "imported_attachments": attachments,
                    "failures": len(failures),
                },
            )
        )
        await session.commit()
        return GmailSyncResult(
            imported_messages=imported,
            imported_attachments=attachments,
            duplicate_messages=duplicates,
            failed_messages=failures,
            next_page_token=listing.get("nextPageToken"),
        )

    async def _resolve_label_ids(self, requested: list[str], headers: dict[str, str]) -> list[str]:
        if not requested:
            return []
        response = await self._request_json("GET", f"{GMAIL_API}/labels", headers=headers)
        lookup: dict[str, str] = {}
        for label in response.get("labels", []):
            label_id = str(label.get("id", "")).strip()
            name = str(label.get("name", "")).strip()
            if label_id:
                lookup[label_id.casefold()] = label_id
            if name and label_id:
                lookup[name.casefold()] = label_id
        resolved: list[str] = []
        for value in requested:
            normalized = value.strip().casefold()
            if normalized not in lookup:
                raise HTTPException(status_code=422, detail=f"Unknown Gmail label: {value}")
            label_id = lookup[normalized]
            if label_id not in resolved:
                resolved.append(label_id)
        return resolved

    async def _refresh_access_token(
        self, session: AsyncSession, connection: GmailConnectionRecord
    ) -> str:
        try:
            refresh_token = self._decrypt(connection.encrypted_refresh_token)
            token = await self._request_json(
                "POST",
                TOKEN_URL,
                data={
                    "client_id": self.settings.google_client_id,
                    "client_secret": self.settings.google_client_secret,
                    "refresh_token": refresh_token,
                    "grant_type": "refresh_token",
                },
            )
            return str(token["access_token"])
        except (HTTPException, KeyError, InvalidToken) as exc:
            connection.status = "REAUTH_REQUIRED"
            connection.last_error = "Google authorization expired or was revoked"
            await session.commit()
            raise HTTPException(status_code=401, detail=connection.last_error) from exc

    async def _connection(
        self, session: AsyncSession, principal: Principal, required: bool = True
    ) -> GmailConnectionRecord | None:
        connection = await session.scalar(
            select(GmailConnectionRecord).where(
                GmailConnectionRecord.tenant_id == principal.tenant_id
            )
        )
        if required and (not connection or connection.status != "CONNECTED"):
            raise HTTPException(status_code=409, detail="Gmail is not connected")
        return connection

    def _decrypt(self, encrypted: str) -> str:
        return self.cipher.decrypt(encrypted.encode()).decode()

    async def _request_json(self, method: str, url: str, allow_empty: bool = False, **kwargs):
        last_response: httpx.Response | None = None
        async with httpx.AsyncClient(timeout=30) as client:
            for attempt in range(3):
                response = await client.request(method, url, **kwargs)
                last_response = response
                if response.status_code not in {429, 500, 502, 503, 504}:
                    break
                try:
                    retry_after = min(float(response.headers.get("Retry-After", "1")), 5)
                except ValueError:
                    retry_after = 1
                await asyncio.sleep(retry_after * (attempt + 1))
        if not last_response or last_response.is_error:
            detail = "Gmail provider request failed"
            if last_response:
                provider_error = ""
                try:
                    payload = last_response.json()
                    provider_error = str(payload.get("error", ""))
                    if isinstance(payload.get("error"), dict):
                        provider_error = str(payload["error"].get("status", ""))
                except (ValueError, TypeError):
                    pass
                if url == TOKEN_URL:
                    if provider_error == "invalid_client" or last_response.status_code == 401:
                        detail = "Google rejected the OAuth client credentials"
                    elif provider_error == "redirect_uri_mismatch":
                        detail = "Google rejected the configured OAuth redirect URI"
                    elif provider_error == "invalid_grant":
                        detail = "Google rejected the one-time authorization code"
                    elif last_response.status_code in {400, 403}:
                        detail = "Google rejected the OAuth token exchange"
                elif url.startswith(GMAIL_API):
                    if last_response.status_code == 400:
                        detail = "Gmail rejected the filters; verify labels and search criteria"
                    if last_response.status_code == 403:
                        detail = (
                            "Gmail API access was denied; enable the Gmail API and verify "
                            "OAuth test-user access"
                        )
                    elif last_response.status_code == 401:
                        detail = "Google rejected the Gmail access token"
            raise HTTPException(status_code=502, detail=detail)
        if allow_empty and not last_response.content:
            return {}
        return last_response.json()

    async def _ingest_attachments(
        self,
        session: AsyncSession,
        principal: Principal,
        case_id: str,
        raw: bytes,
        message_id: str,
    ) -> int:
        message = BytesParser(policy=policy.default).parsebytes(raw)
        count = 0
        allowed_extensions = {
            extension for values in ALLOWED_TYPES.values() for extension in values
        }
        for index, part in enumerate(message.iter_attachments()):
            filename = part.get_filename() or f"attachment-{index}"
            if not any(filename.lower().endswith(extension) for extension in allowed_extensions):
                continue
            data = part.get_payload(decode=True) or b""
            if not data:
                continue
            await self.ingestion.ingest(
                session,
                principal,
                case_id,
                UploadFile(
                    file=BytesIO(data),
                    filename=f"gmail-{message_id}-{filename}",
                    headers=Headers({"content-type": part.get_content_type()}),
                ),
            )
            count += 1
        return count

    @staticmethod
    def _decode_base64url(value: str) -> bytes:
        return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))
