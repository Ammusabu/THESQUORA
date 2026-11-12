"""FastAPI application entry point."""
import logging
import threading
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config.logging_config import configure_logging
from app.config.settings import settings
from app.database.mongo_client import ping
from app.routes.auth_routes import router as auth_router
from app.routes.document_routes import router as document_router
from app.routes.search_routes import router as search_router
from app.routes.chat_routes import router as chat_router
from app.routes.analytics_routes import router as analytics_router

configure_logging()
logger = logging.getLogger(__name__)


def _startup_tasks():
    """Run in a background thread so the port binds immediately."""
    try:
        from app.ml.nltk_setup import ensure_nltk_data
        ensure_nltk_data()
        logger.info("NLTK data ready")
    except Exception as exc:
        logger.error("NLTK setup failed: %s", exc)

    try:
        ok = ping()
        if ok:
            logger.info("MongoDB connected")
        else:
            logger.error("MongoDB ping failed")
    except Exception as exc:
        logger.error("MongoDB check failed: %s", exc)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Bind the port FIRST, do slow work in background
    threading.Thread(target=_startup_tasks, daemon=True).start()
    logger.info("Startup tasks launched in background")
    yield
    logger.info("Shutting down")


app = FastAPI(
    title="THESQUORA API",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_ORIGIN],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(document_router)
app.include_router(search_router)
app.include_router(chat_router)
app.include_router(analytics_router)


@app.get("/api/health", tags=["meta"])
def health():
    try:
        return {"ok": True, "db": ping()}
    except Exception:
        return {"ok": True, "db": False}
