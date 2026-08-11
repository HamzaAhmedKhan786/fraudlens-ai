from collections.abc import Callable
from dataclasses import dataclass
from email import policy
from email.parser import BytesParser
from io import BytesIO


@dataclass(frozen=True)
class ParsedEvidence:
    kind: str
    attributes: dict[str, str | int | float | bool | list[str]]


class EvidenceParser:
    def parse(self, content_type: str, data: bytes) -> ParsedEvidence:
        parsers: dict[str, Callable[[bytes], ParsedEvidence]] = {
            "message/rfc822": self._email,
            "application/pdf": self._pdf,
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document": self._docx,
            "text/plain": self._text,
            "image/png": self._image,
            "image/jpeg": self._image,
        }
        parser = parsers.get(content_type)
        if not parser:
            raise ValueError(f"No parser for {content_type}")
        return parser(data)

    def _email(self, data: bytes) -> ParsedEvidence:
        message = BytesParser(policy=policy.default).parsebytes(data)
        bodies: list[str] = []
        attachments: list[str] = []
        for part in message.walk():
            disposition = part.get_content_disposition()
            if disposition == "attachment":
                attachments.append(part.get_filename() or "unnamed")
            elif part.get_content_type() == "text/plain" and disposition != "attachment":
                try:
                    bodies.append(part.get_content())
                except (LookupError, UnicodeError):
                    pass
        return ParsedEvidence(
            "email",
            {
                "subject": str(message.get("Subject", ""))[:500],
                "from": str(message.get("From", ""))[:500],
                "to": str(message.get("To", ""))[:500],
                "reply_to": str(message.get("Reply-To", ""))[:500],
                "message_id": str(message.get("Message-ID", ""))[:500],
                "attachments": attachments[:100],
                "text_excerpt": "\n".join(bodies)[:10_000],
            },
        )

    def _pdf(self, data: bytes) -> ParsedEvidence:
        from pypdf import PdfReader

        reader = PdfReader(BytesIO(data), strict=False)
        text = "\n".join((page.extract_text() or "") for page in reader.pages)
        metadata = reader.metadata or {}
        return ParsedEvidence(
            "document",
            {
                "page_count": len(reader.pages),
                "title": str(metadata.get("/Title", ""))[:500],
                "author": str(metadata.get("/Author", ""))[:500],
                "producer": str(metadata.get("/Producer", ""))[:500],
                "text_excerpt": text[:10_000],
                "encrypted": bool(reader.is_encrypted),
            },
        )

    def _docx(self, data: bytes) -> ParsedEvidence:
        from docx import Document

        document = Document(BytesIO(data))
        paragraphs = [paragraph.text for paragraph in document.paragraphs if paragraph.text]
        tables = [
            " | ".join(cell.text for cell in row.cells)
            for table in document.tables
            for row in table.rows
        ]
        return ParsedEvidence(
            "document",
            {
                "paragraph_count": len(paragraphs),
                "table_row_count": len(tables),
                "text_excerpt": "\n".join([*paragraphs, *tables])[:10_000],
            },
        )

    def _text(self, data: bytes) -> ParsedEvidence:
        text = data.decode("utf-8", errors="replace")
        return ParsedEvidence(
            "document",
            {"character_count": len(text), "text_excerpt": text[:10_000]},
        )

    def _image(self, data: bytes) -> ParsedEvidence:
        from PIL import ExifTags, Image

        with Image.open(BytesIO(data)) as image:
            exif = {
                str(ExifTags.TAGS.get(key, key)): str(value)[:500]
                for key, value in image.getexif().items()
            }
            return ParsedEvidence(
                "image",
                {
                    "width": image.width,
                    "height": image.height,
                    "format": image.format or "unknown",
                    "mode": image.mode,
                    "exif_keys": sorted(exif.keys())[:100],
                },
            )
