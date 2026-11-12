"""
Index creation for every collection.

Why each index?
- Users: unique email -> fast login lookup + prevents duplicates.
- Documents: compound (owner_id, upload_date) -> "my documents" sorted by newest.
             text index on (title, summary) -> keyword search.
             unique file_hash -> blocks duplicate uploads.
- Chunks: compound (document_id, chunk_index) -> ordered retrieval per doc.
          category + department -> analytics/grouping.
          (Vector index is created separately in Phase 7 via Atlas UI/script.)
- Conversations: (user_id, updated_at) -> "my chats" newest-first.
- Messages: (conversation_id, created_at) -> chronological history per conversation.
- Search logs: (user_id, created_at) for per-user history; TTL purges after 90 days.
"""
import logging
from pymongo import ASCENDING, DESCENDING, TEXT, IndexModel
from pymongo.database import Database

from app.database.collections import (
    USERS, DOCUMENTS, CHUNKS, CONVERSATIONS, MESSAGES, SEARCH_LOGS,
)

logger = logging.getLogger(__name__)


def create_indexes(db: Database) -> None:
    # ---- users ----
    db[USERS].create_indexes([
        IndexModel([("email", ASCENDING)], unique=True, name="uniq_email"),
    ])

    # ---- documents ----
    db[DOCUMENTS].create_indexes([
        IndexModel([("owner_id", ASCENDING), ("upload_date", DESCENDING)],
                   name="owner_recent"),
        IndexModel([("department", ASCENDING), ("category", ASCENDING)],
                   name="dept_category"),
        # Per-user dedupe: the SAME file cannot be uploaded twice by the
        # SAME owner, but different owners may upload identical files.
        # Compound unique -> MongoDB enforces uniqueness atomically at
        # insert time, so concurrent uploads are safe (the loser gets
        # DuplicateKeyError, we translate that to HTTP 409).
        IndexModel(
            [("owner_id", ASCENDING), ("file_hash", ASCENDING)],
            unique=True, sparse=True,
            name="uniq_owner_file_hash",
        ),
        IndexModel([("title", TEXT), ("summary", TEXT)],
                   name="text_title_summary",
                   default_language="english"),
        IndexModel([("processing_status", ASCENDING)], name="status"),
        IndexModel([("cluster_id", ASCENDING)], sparse=True, name="cluster"),
    ])

    # ---- chunks ----
    db[CHUNKS].create_indexes([
        IndexModel([("document_id", ASCENDING), ("chunk_index", ASCENDING)],
                   name="doc_chunk"),
        IndexModel([("text", TEXT)], name="chunks_text",
                   default_language="english"),
        IndexModel([("category", ASCENDING)], name="category"),
        IndexModel([("owner_id", ASCENDING)], name="owner"),
    ])

    # ---- conversations ----
    db[CONVERSATIONS].create_indexes([
        IndexModel([("user_id", ASCENDING), ("updated_at", DESCENDING)],
                   name="user_recent"),
    ])

    # ---- messages ----
    db[MESSAGES].create_indexes([
        IndexModel([("conversation_id", ASCENDING), ("created_at", ASCENDING)],
                   name="conv_chrono"),
    ])

    # ---- search_logs ----
    db[SEARCH_LOGS].create_indexes([
        IndexModel([("user_id", ASCENDING), ("created_at", DESCENDING)],
                   name="user_recent"),
        IndexModel([("query", ASCENDING)], name="query"),
        # TTL: purge logs older than 90 days automatically.
        IndexModel([("created_at", ASCENDING)], expireAfterSeconds=60 * 60 * 24 * 90,
                   name="ttl_90d"),
    ])

    logger.info("Indexes created/verified for all collections")
