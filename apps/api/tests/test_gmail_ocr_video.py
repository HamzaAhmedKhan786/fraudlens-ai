import base64
from io import BytesIO
from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from fraudlens.auth import Principal
from fraudlens.config import Settings
from fraudlens.gmail import GmailConnector
from fraudlens.parsers import EvidenceParser
from fraudlens.schemas import GmailSyncRequest
from fraudlens.video import DisabledVideoInferenceAdapter, VideoInferenceRequest
from PIL import Image


class FakeIngestion:
    pass


class FakeSession:
    def __init__(self, fetched=None) -> None:
        self.added = None
        self.fetched = fetched
        self.commits = 0

    def add(self, value) -> None:
        self.added = value

    async def commit(self) -> None:
        self.commits += 1

    async def get(self, *args, **kwargs):
        return self.fetched

    async def scalar(self, *args, **kwargs):
        return self.fetched

    async def execute(self, *args, **kwargs):
        return None


def finish(coroutine):
    try:
        coroutine.send(None)
    except StopIteration as completed:
        return completed.value
    raise AssertionError("Test coroutine unexpectedly required external I/O")


def settings(**overrides) -> Settings:
    return Settings(
        api_key="a" * 32,
        google_client_id="client-id",
        google_client_secret="client-secret",
        **overrides,
    )


def test_oauth_state_is_random_hashed_and_not_persisted_in_plaintext() -> None:
    session = FakeSession()
    connector = GmailConnector(settings(), FakeIngestion())
    principal = Principal(subject="analyst", tenant_id="tenant-a", roles=frozenset({"analyst"}))
    url = finish(connector.authorization_url(session, principal))
    state = url.split("state=", 1)[1].split("&", 1)[0]
    assert state not in session.added.state_hash
    assert len(session.added.state_hash) == 64
    assert session.added.tenant_id == "tenant-a"


def test_oauth_callback_rejects_unknown_state_before_token_exchange() -> None:
    session = FakeSession()
    connector = GmailConnector(settings(), FakeIngestion())
    with pytest.raises(HTTPException, match="Invalid or expired OAuth state"):
        finish(connector.callback(session, "unknown-state-value-that-is-long-enough", "code"))


def test_refresh_token_is_encrypted_and_refresh_failure_requires_reauth() -> None:
    connector = GmailConnector(settings(), FakeIngestion())
    ciphertext = connector.cipher.encrypt(b"refresh-secret").decode()
    assert "refresh-secret" not in ciphertext
    connection = SimpleNamespace(
        encrypted_refresh_token=ciphertext, status="CONNECTED", last_error=None
    )
    session = FakeSession()

    async def failed_request(*args, **kwargs):
        raise HTTPException(status_code=502, detail="failed")

    connector._request_json = failed_request
    with pytest.raises(HTTPException) as error:
        finish(connector._refresh_access_token(session, connection))
    assert error.value.status_code == 401
    assert connection.status == "REAUTH_REQUIRED"


def test_refresh_token_exchange_returns_new_access_token() -> None:
    connector = GmailConnector(settings(), FakeIngestion())
    connection = SimpleNamespace(
        encrypted_refresh_token=connector.cipher.encrypt(b"refresh-secret").decode(),
        status="CONNECTED",
        last_error=None,
    )

    async def refreshed(method, url, **kwargs):
        assert kwargs["data"]["refresh_token"] == "refresh-secret"
        return {"access_token": "new-access-token"}

    connector._request_json = refreshed
    assert finish(connector._refresh_access_token(FakeSession(), connection)) == "new-access-token"


def test_email_parser_extracts_authentication_results() -> None:
    raw = (
        b"From: sender@example.com\r\nTo: analyst@example.com\r\nSubject: test\r\n"
        b"Authentication-Results: mx.example; spf=pass; dkim=pass; dmarc=pass\r\n\r\nBody"
    )
    attributes = EvidenceParser().parse("message/rfc822", raw).attributes
    assert attributes["spf_pass"] is True
    assert attributes["dkim_pass"] is True
    assert attributes["dmarc_pass"] is True


def test_ocr_failure_is_explicit_and_does_not_claim_authenticity() -> None:
    image = Image.new("RGB", (120, 40), "white")
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    parser = EvidenceParser(
        settings(ocr_enabled=True, tesseract_cmd="missing-tesseract-executable")
    )
    attributes = parser.parse("image/png", buffer.getvalue()).attributes
    assert attributes["ocr_status"] == "FAILED"
    assert attributes["ocr_authenticity_verified"] is False
    assert attributes["ocr_error"]


def test_disabled_video_adapter_returns_uncertain_failure_not_success() -> None:
    result = finish(
        DisabledVideoInferenceAdapter().infer(
            VideoInferenceRequest(object_uri="gs://fraudlens/video.mp4")
        )
    )
    assert result.status == "NOT_CONFIGURED"
    assert result.classification == "UNKNOWN"
    assert result.experimental is True
    assert result.confidence is None


def test_gmail_raw_base64url_decoding() -> None:
    raw = b"Subject: test\r\n\r\nbody"
    encoded = base64.urlsafe_b64encode(raw).decode().rstrip("=")
    assert GmailConnector._decode_base64url(encoded) == raw


def test_gmail_sync_ingests_raw_message_and_returns_pagination() -> None:
    raw = b"From: sender@example.com\r\nTo: analyst@example.com\r\nSubject: Invoice\r\n\r\nBody"

    class Ingestion:
        total = 0

        async def list(self, session, principal, case_id):
            return SimpleNamespace(total=self.total)

        async def ingest(self, session, principal, case_id, upload):
            assert case_id == "CASE-1"
            assert upload.filename == "gmail-message-1.eml"
            self.total += 1
            return SimpleNamespace(status="PROCESSED", error=None)

    connection = SimpleNamespace(
        status="CONNECTED",
        email_address="tester@example.com",
        last_sync_at=None,
        last_error=None,
    )
    session = FakeSession(connection)
    connector = GmailConnector(settings(), Ingestion())

    async def access_token(*args, **kwargs):
        return "access"

    async def google(method, url, **kwargs):
        if url.endswith("/messages"):
            return {"messages": [{"id": "message-1"}], "nextPageToken": "next"}
        return {"raw": base64.urlsafe_b64encode(raw).decode().rstrip("=")}

    connector._refresh_access_token = access_token
    connector._request_json = google
    principal = Principal(subject="analyst", tenant_id="tenant-a", roles=frozenset({"analyst"}))
    result = finish(
        connector.sync(
            session, principal, GmailSyncRequest(case_id="CASE-1", sender="sender@example.com")
        )
    )
    assert result.imported_messages == 1
    assert result.duplicate_messages == 0
    assert result.next_page_token == "next"
    assert connection.last_sync_at is not None
