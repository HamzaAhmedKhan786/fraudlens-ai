from io import BytesIO
from pathlib import PurePath
from zipfile import BadZipFile, ZipFile

import filetype

ALLOWED_TYPES = {
    "message/rfc822": {".eml"},
    "application/pdf": {".pdf"},
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": {".docx"},
    "text/plain": {".txt"},
    "image/png": {".png"},
    "image/jpeg": {".jpg", ".jpeg"},
}


def safe_filename(value: str | None) -> str:
    if not value or "\0" in value:
        raise ValueError("A valid filename is required")
    name = PurePath(value.replace("\\", "/")).name
    if name in {"", ".", ".."} or len(name) > 255:
        raise ValueError("Invalid filename")
    return name


def detect_content_type(data: bytes, filename: str) -> str:
    suffix = PurePath(filename).suffix.lower()
    kind = filetype.guess(data[:8192])
    detected = kind.mime if kind else None
    if data.startswith(b"%PDF-"):
        detected = "application/pdf"
    elif suffix == ".eml" and (b"From:" in data[:8192] or b"Subject:" in data[:8192]):
        detected = "message/rfc822"
    elif suffix == ".txt" and b"\0" not in data[:8192]:
        detected = "text/plain"
    elif suffix == ".docx" and _is_docx(data):
        detected = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    if detected not in ALLOWED_TYPES or suffix not in ALLOWED_TYPES[detected]:
        raise ValueError("File content or extension is not an allowed evidence type")
    return detected


def _is_docx(data: bytes) -> bool:
    try:
        with ZipFile(BytesIO(data)) as archive:
            names = set(archive.namelist())
            return "[Content_Types].xml" in names and "word/document.xml" in names
    except (BadZipFile, OSError):
        return False
