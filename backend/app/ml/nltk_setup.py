"""
Ensure NLTK data (stopwords, punkt) is downloaded at startup.
On Render the first deploy won't have cached NLTK data, so we download
it once into the local cache. Subsequent deploys use the cached version.
"""
import logging

logger = logging.getLogger(__name__)


def ensure_nltk_data() -> None:
    """Download NLTK resources if not already present."""
    try:
        import nltk
    except ImportError:
        logger.warning("nltk not installed — skipping data download")
        return

    for resource in [
        ("corpora", "stopwords"),
        ("tokenizers", "punkt"),
        ("tokenizers", "punkt_tab"),
    ]:
        try:
            nltk.data.find(f"{resource[0]}/{resource[1]}")
            logger.info("NLTK resource '%s/%s' already present", *resource)
        except LookupError:
            logger.info("Downloading NLTK resource '%s/%s'...", *resource)
            nltk.download(resource[1], quiet=True)
