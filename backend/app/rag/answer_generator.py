"""
Orchestrates: retrieve -> build prompt -> call LLM -> extract citations.

Citations are derived from the actual context chunks we fed the model,
not from parsing free-form text. That guarantees the source list is truthful
(the model may cite [3] but we still attach the real doc/page for [3]).
"""
from __future__ import annotations

import logging
import re

from app.rag import llm_client
from app.rag.prompt_builder import build_messages
from app.rag.retriever import retrieve

logger = logging.getLogger(__name__)

_CITE_RE = re.compile(r"\[(\d+)\]")


def _build_sources(chunks: list[dict]) -> list[dict]:
    return [
        {
            "n": i + 1,
            "document_id": str(c["document_id"]),
            "title": c.get("document_title") or "(unknown)",
            "page_number": c.get("page_number"),
            "chunk_index": c.get("chunk_index"),
            "snippet": (c.get("text") or "")[:240],
        }
        for i, c in enumerate(chunks)
    ]


# Phrases the model uses when it refuses to answer.
_REFUSAL_MARKERS = (
    "do not contain enough information",
    "does not contain enough information",
    "not enough information",
    "no relevant information",
    "cannot answer",
    "don't know",
    "do not know",
    "unable to answer",
)


def _looks_like_refusal(answer: str) -> bool:
    a = (answer or "").lower()
    return any(marker in a for marker in _REFUSAL_MARKERS)


def _filter_cited_sources(answer: str, all_sources: list[dict]) -> list[dict]:
    """
    Return only sources the answer actually cited as [n].
    - If the answer contains citations -> return those sources.
    - If the answer is a refusal -> return [] (the retrieved context did not
      support an answer, so listing it as "sources" would be misleading).
    - If the answer has substance but no [n] citations -> return all sources
      (defensive: the model used them as context, just forgot to cite).
    """
    nums = {int(m) for m in _CITE_RE.findall(answer)}
    if nums:
        return [s for s in all_sources if s["n"] in nums]
    if _looks_like_refusal(answer):
        return []
    if len(answer.strip()) < 20:
        return []
    return all_sources


def generate_answer(
    *,
    current_user: dict,
    question: str,
    history: list[dict] | None = None,
    top_k: int = 5,
) -> dict:
    chunks = retrieve(current_user=current_user, query=question, top_k=top_k)
    messages = build_messages(
        question=question, chunks=chunks, history=history,
    )
    try:
        llm = llm_client.chat(messages)
    except RuntimeError as exc:
        raise RuntimeError(str(exc)) from exc

    all_sources = _build_sources(chunks)
    cited = _filter_cited_sources(llm["content"], all_sources)

    return {
        "answer": llm["content"].strip(),
        "sources": cited,
        "context_used": len(chunks),
        "model": llm["model"],
        "usage": llm["usage"],
    }
