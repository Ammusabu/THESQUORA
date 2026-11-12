"""
Idempotent database bootstrap:
1) Create each collection with a $jsonSchema validator (or update the validator).
2) Create indexes.
3) Print a summary.

Run from the backend folder:
    python -m app.database.setup_db
"""
import logging

from pymongo.database import Database
from pymongo.errors import CollectionInvalid, OperationFailure

from app.config.logging_config import configure_logging
from app.database.collections import (
    USERS, DOCUMENTS, CHUNKS, CONVERSATIONS, MESSAGES, SEARCH_LOGS, ALL_COLLECTIONS,
)
from app.database.indexes import create_indexes
from app.database.mongo_client import get_db, ping
from app.database.schemas import (
    USER_SCHEMA, DOCUMENT_SCHEMA, CHUNK_SCHEMA,
    CONVERSATION_SCHEMA, MESSAGE_SCHEMA, SEARCH_LOG_SCHEMA,
)

logger = logging.getLogger(__name__)

SCHEMAS = {
    USERS: USER_SCHEMA,
    DOCUMENTS: DOCUMENT_SCHEMA,
    CHUNKS: CHUNK_SCHEMA,
    CONVERSATIONS: CONVERSATION_SCHEMA,
    MESSAGES: MESSAGE_SCHEMA,
    SEARCH_LOGS: SEARCH_LOG_SCHEMA,
}


def ensure_collection(db: Database, name: str, schema: dict) -> None:
    existing = set(db.list_collection_names())
    if name not in existing:
        try:
            db.create_collection(
                name,
                validator=schema,
                validationLevel="strict",
                validationAction="error",
            )
            logger.info("Created collection %s with validator", name)
            return
        except CollectionInvalid as exc:
            logger.warning("Collection %s already existed: %s", name, exc)

    # Existing collection -> refresh the validator (idempotent update)
    try:
        db.command({
            "collMod": name,
            "validator": schema,
            "validationLevel": "strict",
            "validationAction": "error",
        })
        logger.info("Updated validator on %s", name)
    except OperationFailure as exc:
        logger.error("Failed to update validator on %s: %s", name, exc)
        raise


def main() -> None:
    configure_logging()
    if not ping():
        raise SystemExit("Cannot reach MongoDB. Check MONGO_URI in .env")

    db = get_db()
    logger.info("Connected to MongoDB database: %s", db.name)

    for name in ALL_COLLECTIONS:
        ensure_collection(db, name, SCHEMAS[name])

    create_indexes(db)

    # Summary
    print("\n=== THESQORA DB SUMMARY ===")
    print(f"Database: {db.name}")
    for name in ALL_COLLECTIONS:
        idx_names = [ix["name"] for ix in db[name].list_indexes()]
        count = db[name].estimated_document_count()
        print(f"- {name:15s} docs={count:<5d} indexes={idx_names}")
    print("===========================\n")


if __name__ == "__main__":
    main()
