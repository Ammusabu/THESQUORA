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
    if not ping():
        logger.error("MongoDB ping failed at startup — check MONGO_URI")
    else:
        logger.info("MongoDB connection healthy")
    try:
        from app.ml.embeddings import embed_text
        embed_text("warmup")  # forces model download + load once
        logger.info("Embedding model warm")
    except Exception as exc:
        logger.error("Embedding model failed to load: %s", exc)
    yield
    logger.info("Shutting down")


app = FastAPI(
    title="THESQORA API",
    version="0.3.0",
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
