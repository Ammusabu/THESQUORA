"""
Text preprocessing shared by classification and (later) chunking.

Steps:
  lowercase -> strip punctuation/digits -> collapse whitespace -> filter tokens
  Keep tokens with len>=2, drop NLTK English stopwords.

Why this order:
- Lowercasing removes spurious distinct features ("API" vs "api").
- Punctuation/digit removal prevents tokens like "12%" from dominating.
- Stopword removal focuses the vectorizer on content-bearing words.
"""
import re
import string

import nltk
from nltk.corpus import stopwords as nltk_stopwords

_PUNCT_RE = re.compile(f"[{re.escape(string.punctuation)}]")
_DIGIT_RE = re.compile(r"\d+")
_WS_RE = re.compile(r"\s+")

_STOPWORDS: set[str] | None = None


def _ensure_nltk() -> None:
    global _STOPWORDS
    if _STOPWORDS is not None:
        return
    try:
        nltk_stopwords.words("english")
    except LookupError:
        nltk.download("stopwords", quiet=True)
        nltk.download("punkt", quiet=True)
    _STOPWORDS = set(nltk_stopwords.words("english"))


def clean_text(text: str) -> str:
    _ensure_nltk()
    text = text.lower()
    text = _PUNCT_RE.sub(" ", text)
    text = _DIGIT_RE.sub(" ", text)
    text = _WS_RE.sub(" ", text).strip()
    tokens = [t for t in text.split() if len(t) >= 2 and t not in _STOPWORDS]  # type: ignore[operator]
    return " ".join(tokens)
