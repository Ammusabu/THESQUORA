"""
Train + evaluate the classifier and print an honest report.

Run:
    python -m scripts.train_classifier
"""
import json
import logging

from app.config.logging_config import configure_logging
from app.ml.classifier import METRICS_PATH, load_seed_corpus, train

configure_logging()
logger = logging.getLogger(__name__)


def main() -> None:
    texts, labels = load_seed_corpus(
        __import__("pathlib").Path(__file__).parents[1] / "app/ml/data/seed_corpus.txt"
    )
    logger.info("Loaded %d examples across %d classes", len(texts), len(set(labels)))

    metrics = train(texts, labels)

    print("\n=== CLASSIFICATION REPORT ===")
    for key in ("logreg", "naive_bayes"):
        m = metrics[key]
        rep = m["report"]
        print(f"\n[{m['name']}] accuracy = {m['accuracy']:.3f}")
        print(f"  macro P/R/F1 = "
              f"{rep['macro avg']['precision']:.3f} / "
              f"{rep['macro avg']['recall']:.3f} / "
              f"{rep['macro avg']['f1-score']:.3f}")
        print(f"  weighted F1  = {rep['weighted avg']['f1-score']:.3f}")
        print("  per-class F1:")
        for cls, row in rep.items():
            if cls in ("accuracy", "macro avg", "weighted avg"):
                continue
            print(f"    {cls:10s} P={row['precision']:.2f} R={row['recall']:.2f} F1={row['f1-score']:.2f} n={int(row['support'])}")

    print(f"\nArtifacts saved under app/ml/artifacts/")
    print(f"Metrics JSON: {METRICS_PATH}")
    print("============================\n")


if __name__ == "__main__":
    main()
