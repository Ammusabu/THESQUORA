"""
Text extraction for PDF / DOCX / TXT.

Returns a list of "pages" where each element is the extracted text of one
page (PDF) or a single element (DOCX/TXT). Keeping page boundaries lets us
record per-chunk page numbers later (Phase 6).
"""
import io
import logging

from fastapi import HTTPException, status
from pypdf import PdfReader
from docx import Document as DocxDocument

logger = logging.getLogger(__name__)


def _extract_pdf(raw: bytes) -> list[str]:
    try:
        reader = PdfReader(io.BytesIO(raw))
        pages: list[str] = []
        for p in reader.pages:
            try:
                pages.append(p.extract_text() or "")
            except Exception as exc:  # noqa: BLE001
                logger.warning("PDF page extraction failed: %s", exc)
                pages.append("")
        return pages
    except Exception as exc:
        logger.exception("PDF parse error: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Corrupted or unreadable PDF",
        )


def _extract_docx(raw: bytes) -> list[str]:
    try:
        doc = DocxDocument(io.BytesIO(raw))
        text = "\n".join(p.text for p in doc.paragraphs)
        return [text]
    except Exception as exc:
        logger.exception("DOCX parse error: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Corrupted or unreadable DOCX",
        )


def _extract_txt(raw: bytes) -> list[str]:
    for enc in ("utf-8", "utf-16", "latin-1"):
        try:
            return [raw.decode(enc)]
        except UnicodeDecodeError:
            continue
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Unable to decode TXT file",
    )


def extract_text(raw: bytes, ext: str) -> list[str]:
    if ext == "pdf":
        pages = _extract_pdf(raw)
    elif ext == "docx":
        pages = _extract_docx(raw)
    elif ext == "txt":
        pages = _extract_txt(raw)
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported ext {ext}")

    joined = "".join(pages).strip()
    if not joined:
        raise HTTPException(
            status_code=400,
            detail="No extractable text found (document may be scanned/image-only)",
        )
    return pages
