"""MongoDB client singleton."""
import logging
import certifi
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
            tlsCAFile=certifi.where(),
            appname="thesquora-backend",
        )
    return _client


def get_db() -> Database:
    return get_client()[settings.MONGO_DB_NAME]


def ping() -> bool:
    try:
        get_client().admin.command("ping")
        return True
    except Exception as exc:
        logger.error("MongoDB ping failed: %s", exc)
        return False
