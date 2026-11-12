"""
Character-based sliding-window chunker with overlap and page tracking.

Why characters, not tokens?
- Simple, dependency-free, deterministic.
- ~800 chars ≈ 150–200 tokens for English — well within MiniLM's 256-token limit.

Why overlap?
- A sentence straddling a boundary is present in at least one chunk.
- 150-char overlap ≈ one long sentence safety margin.

Page tracking:
- We process one page at a time so each chunk knows which page it came from.
- PDFs have meaningful pages; DOCX/TXT are single-page.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Chunk:
    chunk_index: int
    text: str
    page_number: int | None


def _chunk_page(page_text: str, size: int, overlap: int) -> list[str]:
    text = page_text.strip()
    if not text:
        return []
    if len(text) <= size:
        return [text]

    chunks: list[str] = []
    start = 0
    n = len(text)
    while start < n:
        end = min(start + size, n)
        piece = text[start:end].strip()
        if piece:
            chunks.append(piece)
        if end == n:
            break
        start = max(end - overlap, start + 1)
    return chunks


def chunk_pages(
    pages: list[str],
    *,
    chunk_size: int,
    overlap: int,
) -> list[Chunk]:
    """Turn list-of-pages into a flat list of numbered, page-tagged chunks."""
    if chunk_size <= 0:
        raise ValueError("chunk_size must be > 0")
    if overlap < 0 or overlap >= chunk_size:
        raise ValueError("overlap must satisfy 0 <= overlap < chunk_size")

    out: list[Chunk] = []
    idx = 0
    for page_no, page_text in enumerate(pages, start=1):
        for piece in _chunk_page(page_text, chunk_size, overlap):
            out.append(Chunk(chunk_index=idx, text=piece, page_number=page_no))
            idx += 1
    return out
