from fraudlens.file_security import detect_content_type, safe_filename
from fraudlens.parsers import EvidenceParser
from fraudlens.scanner import VirusScanner


def test_filename_is_reduced_to_safe_basename() -> None:
    assert safe_filename("../../supplier/invoice.txt") == "invoice.txt"
    assert detect_content_type(b"invoice total: 4000", "invoice.txt") == "text/plain"


def test_email_parser_extracts_headers_body_and_attachments() -> None:
    parsed = EvidenceParser().parse(
        "message/rfc822",
        (
            b"From: sender@example.com\r\nTo: analyst@example.com\r\n"
            b"Subject: Payment\r\n\r\nTransfer today."
        ),
    )
    assert parsed.kind == "email"
    assert parsed.attributes["subject"] == "Payment"
    assert "Transfer today" in str(parsed.attributes["text_excerpt"])


def test_document_parser_extracts_payment_risk_indicators() -> None:
    parsed = EvidenceParser().parse(
        "text/plain",
        (
            b"Our bank details have changed. Use the new IBAN "
            b"DE89370400440532013000 for this urgent payment today."
        ),
    )
    assert parsed.attributes["payment_change_language"] is True
    assert parsed.attributes["urgent_payment_language"] is True
    assert parsed.attributes["ibans"] == ["DE89370400440532013000"]


def test_benign_document_does_not_invent_risk_indicators() -> None:
    parsed = EvidenceParser().parse(
        "text/plain", b"Quarterly product catalogue and standard delivery information."
    )
    assert parsed.attributes["payment_change_language"] is False
    assert parsed.attributes["urgent_payment_language"] is False
    assert parsed.attributes["ibans"] == []


async def test_disabled_scanner_is_explicitly_skipped() -> None:
    result = await VirusScanner(False, False, "localhost", 3310).scan(b"evidence")
    assert result.status == "SKIPPED"
