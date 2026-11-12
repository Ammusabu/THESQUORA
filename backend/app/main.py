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
    try:
        from app.ml.nltk_setup import ensure_nltk_data
        ensure_nltk_data()
        logger.info("NLTK data ready")
    except Exception as exc:
        logger.error("NLTK setup failed: %s", exc)

    try:
        if ping():
            logger.info("MongoDB connected")
        else:
            logger.error("MongoDB ping failed")
    except Exception as exc:
        logger.error("MongoDB check failed: %s", exc)


@asynccontextmanager
async def lifespan(app: FastAPI):
    threading.Thread(target=_startup_tasks, daemon=True).start()
    logger.info("Startup tasks launched in background")
    yield
    logger.info("Shutting down")


app = FastAPI(
    title="THESQUORA API",
    version="1.0.0",
    lifespan=lifespan,
)

# ============================================================
# CORS — explicit origins only, no regex surprises
# ============================================================
# Build the allowed origins list from the environment.
# - settings.FRONTEND_ORIGIN is the production URL from .env
# - We also hardcode the two most common Vercel preview patterns
allowed_origins = [
    settings.FRONTEND_ORIGIN,
    "http://localhost:5173",
    "https://thesquora.vercel.app",
]
# Dedupe while preserving order
seen = set()
allowed_origins = [x for x in allowed_origins if not (x in seen or seen.add(x))]

logger.info("CORS allowed origins: %s", allowed_origins)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    # allow_origin_regex=None is the default — we rely on allow_origins
    # (using BOTH allow_origins and allow_origin_regex causes subtle bugs)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# ============================================================
# Routers
# ============================================================
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
