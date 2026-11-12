"""FastAPI application entry point."""
import logging
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


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Only lightweight startup tasks — models load lazily on first request
    try:
        from app.ml.nltk_setup import ensure_nltk_data
        ensure_nltk_data()
    except Exception as exc:
        logger.error("NLTK setup failed: %s", exc)

    if not ping():
        logger.error("MongoDB ping failed — check MONGO_URI")
    else:
        logger.info("MongoDB connection healthy")

    logger.info("Startup complete (models will load on first request)")
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
    return {"ok": True, "db": ping()}
