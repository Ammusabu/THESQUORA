"""Re-run the chunk+embed pipeline on every document that has _extracted_pages."""
from app.config.logging_config import configure_logging
from app.database.collections import DOCUMENTS
from app.database.mongo_client import get_db
from app.services.processing_service import process_document
import logging

configure_logging()
logger = logging.getLogger(__name__)

def main():
    db = get_db()
    for doc in db[DOCUMENTS].find({}, {"_id": 1, "title": 1}):
        did = str(doc["_id"])
        try:
            res = process_document(did)
            print(f"✅ {doc['title'][:40]:42s} chunks={res['chunks']}")
        except Exception as exc:
            print(f"❌ {doc['title'][:40]:42s} {exc}")

if __name__ == "__main__":
    main()
