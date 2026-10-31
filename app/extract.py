"""Validate uploads and pull text out of them. Files are processed in memory, never written to disk."""
from __future__ import annotations

import io
import re
from pathlib import Path

from .config import Settings

ALLOWED_EXTENSIONS = {".txt", ".md", ".pdf"}


class UploadError(Exception):
    def __init__(self, message: str, status: int = 400):
        super().__init__(message)
        self.status = status


def safe_name(filename: str | None) -> str:
    name = Path(filename or "evidence.txt").name
    name = re.sub(r"[\x00-\x1f<>\"'`\\]", "", name).strip()
    return name[:100] or "evidence.txt"


def extract_text(name: str, content: bytes, settings: Settings) -> str:
    ext = Path(name).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise UploadError(f"'{name}': unsupported file type. Use TXT, MD or PDF.")
    if ext in {".txt", ".md"}:
        if b"\x00" in content[:4096]:
            raise UploadError(f"'{name}' looks like a binary file, not text.")
        return content.decode("utf-8", errors="replace")

    if not content.startswith(b"%PDF-"):
        raise UploadError(f"'{name}' is not a valid PDF.")
    from pypdf import PdfReader

    try:
        reader = PdfReader(io.BytesIO(content))
        if reader.is_encrypted and not reader.decrypt(""):
            raise UploadError(f"'{name}' is password protected.")
        pages = []
        for number, page in enumerate(reader.pages[: settings.max_pdf_pages], start=1):
            pages.append(f"[Page {number}]\n{page.extract_text() or ''}")
    except UploadError:
        raise
    except Exception as exc:  # noqa: BLE001 - pypdf raises many types on malformed files
        raise UploadError(f"'{name}' could not be read as a PDF.") from exc
    return "\n".join(pages)
