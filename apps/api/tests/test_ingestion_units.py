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


async def test_disabled_scanner_is_explicitly_skipped() -> None:
    result = await VirusScanner(False, False, "localhost", 3310).scan(b"evidence")
    assert result.status == "SKIPPED"
