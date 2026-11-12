"""
Document classification: TF-IDF + LogisticRegression (primary),
MultinomialNB (baseline).

Artifacts saved with joblib under app/ml/artifacts/:
  - vectorizer.joblib   (TfidfVectorizer fitted on training text)
  - logreg.joblib       (primary classifier)
  - nb.joblib           (baseline)
  - labels.joblib       (sorted class names, for reference)
  - metrics.json        (evaluation report)
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Iterable

import joblib
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score, classification_report, confusion_matrix,
)
from sklearn.model_selection import train_test_split
from sklearn.naive_bayes import MultinomialNB

from app.ml.preprocess import clean_text

logger = logging.getLogger(__name__)

ARTIFACTS = Path(__file__).parent / "artifacts"
ARTIFACTS.mkdir(parents=True, exist_ok=True)

VEC_PATH = ARTIFACTS / "vectorizer.joblib"
LOGREG_PATH = ARTIFACTS / "logreg.joblib"
NB_PATH = ARTIFACTS / "nb.joblib"
LABELS_PATH = ARTIFACTS / "labels.joblib"
METRICS_PATH = ARTIFACTS / "metrics.json"


# ---------- data loading ----------
def load_seed_corpus(path: Path) -> tuple[list[str], list[str]]:
    texts: list[str] = []
    labels: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip() or "|" not in line:
            continue
        label, text = line.split("|", 1)
        texts.append(text.strip())
        labels.append(label.strip())
    return texts, labels


# ---------- training ----------
def train(
    texts: Iterable[str],
    labels: Iterable[str],
    *,
    test_size: float = 0.25,
    random_state: int = 42,
) -> dict:
    texts = [clean_text(t) for t in texts]
    labels = list(labels)

    if len(set(labels)) < 2:
        raise ValueError("Need at least 2 classes to train")

    X_train_txt, X_test_txt, y_train, y_test = train_test_split(
        texts, labels,
        test_size=test_size,
        random_state=random_state,
        stratify=labels,
    )

    vectorizer = TfidfVectorizer(
        ngram_range=(1, 2),   # unigrams + bigrams — captures "annual leave", "vector search"
        min_df=1,
        max_df=0.95,          # drop terms appearing in >95% of docs (near-useless)
        sublinear_tf=True,    # log(1+tf) dampens very frequent terms
    )
    X_train = vectorizer.fit_transform(X_train_txt)
    X_test = vectorizer.transform(X_test_txt)

    logreg = LogisticRegression(
        max_iter=1000,
        C=1.0,
        class_weight="balanced",  # helps since classes may be slightly uneven
        n_jobs=None,
    )
    logreg.fit(X_train, y_train)

    nb = MultinomialNB(alpha=1.0)
    nb.fit(X_train, y_train)

    # ---------- evaluate ----------
    def _report(name: str, y_pred: np.ndarray) -> dict:
        acc = float(accuracy_score(y_test, y_pred))
        rep = classification_report(y_test, y_pred, output_dict=True, zero_division=0)
        cm = confusion_matrix(y_test, y_pred, labels=sorted(set(labels))).tolist()
        return {"name": name, "accuracy": acc, "report": rep, "confusion_matrix": cm}

    lr_metrics = _report("logreg", logreg.predict(X_test))
    nb_metrics = _report("naive_bayes", nb.predict(X_test))

    payload = {
        "n_train": int(len(y_train)),
        "n_test": int(len(y_test)),
        "classes": sorted(set(labels)),
        "logreg": lr_metrics,
        "naive_bayes": nb_metrics,
    }

    # ---------- persist ----------
    joblib.dump(vectorizer, VEC_PATH)
    joblib.dump(logreg, LOGREG_PATH)
    joblib.dump(nb, NB_PATH)
    joblib.dump(sorted(set(labels)), LABELS_PATH)
    METRICS_PATH.write_text(json.dumps(payload, indent=2))
    logger.info("Trained + persisted. LogReg acc=%.3f NB acc=%.3f",
                lr_metrics["accuracy"], nb_metrics["accuracy"])
    return payload


# ---------- inference ----------
_state: dict | None = None


def _load() -> dict:
    global _state
    if _state is None:
        if not all(p.exists() for p in (VEC_PATH, LOGREG_PATH)):
            raise RuntimeError("Classifier not trained. Run: python -m scripts.train_classifier")
        _state = {
            "vectorizer": joblib.load(VEC_PATH),
            "logreg": joblib.load(LOGREG_PATH),
            "nb": joblib.load(NB_PATH) if NB_PATH.exists() else None,
        }
    return _state


def predict(text: str) -> tuple[str, float]:
    """Return (category, confidence). Confidence is the probability of the
    winning class from LogisticRegression.predict_proba."""
    state = _load()
    cleaned = clean_text(text)
    if not cleaned.strip():
        return "General", 0.0
    X = state["vectorizer"].transform([cleaned])
    logreg = state["logreg"]
    probs = logreg.predict_proba(X)[0]
    idx = int(np.argmax(probs))
    label = logreg.classes_[idx]
    return str(label), float(probs[idx])
