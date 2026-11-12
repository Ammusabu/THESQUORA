"""
MongoDB client singleton.

Why a singleton?
- MongoClient manages an internal connection pool. Creating one per request
  would exhaust sockets. We create it once at startup and reuse it.
- PyMongo's MongoClient is thread-safe, so reuse is safe across FastAPI
  threadpool workers.
"""
import logging
from pymongo import MongoClient
from pymongo.database import Database

from app.config.settings import settings

logger = logging.getLogger(__name__)

_client: MongoClient | None = None


def get_client() -> MongoClient:
    global _client
    if _client is None:
        logger.info("Creating MongoDB client (singleton)")
        _client = MongoClient(
            settings.MONGO_URI,
            serverSelectionTimeoutMS=10_000,
            appname="thesqora-backend",
        )
    return _client


def get_db() -> Database:
    return get_client()[settings.MONGO_DB_NAME]


def ping() -> bool:
    """Health check — returns True if the cluster responds."""
    try:
        get_client().admin.command("ping")
        return True
    except Exception as exc:  # noqa: BLE001
        logger.error("MongoDB ping failed: %s", exc)
        return False
