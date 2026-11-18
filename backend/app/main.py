"""EstateIQ FastAPI application — production-safe startup."""

import os
import threading
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import get_settings
from app.core.logging import setup_logging, get_logger

setup_logging()
logger = get_logger(__name__)
settings = get_settings()


def _background_ingest():
    """Run ingestion in a background thread so the port binds immediately."""
    try:
        from app.rag.vectorstore import get_collection_stats
        stats = get_collection_stats(settings.chroma_persist_dir)
        total = sum(stats.values())
        if total > 0:
            logger.info(f"ChromaDB already has {total} chunks — skipping ingestion.")
            return
        logger.info("Starting background ingestion...")
        from app.services.ingestion_service import run_ingestion
        result = run_ingestion(sources=["darglobal", "wasalt"], force_refresh=False)
        logger.info(
            f"Background ingestion complete: "
            f"{result['total_documents']} docs, {result['indexed_chunks']} chunks"
        )
    except Exception as e:
        logger.error(f"Background ingestion failed: {e}", exc_info=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("EstateIQ Backend starting — binding port immediately")

    # Ensure directories exist
    Path(settings.chroma_persist_dir).mkdir(parents=True, exist_ok=True)
    Path("./data/raw").mkdir(parents=True, exist_ok=True)
    Path("./data/processed").mkdir(parents=True, exist_ok=True)

    # Start ingestion in background — port binds first
    t = threading.Thread(target=_background_ingest, daemon=True)
    t.start()

    yield
    logger.info("EstateIQ Backend shutting down.")


app = FastAPI(
    title="EstateIQ API",
    description="AI real estate assistant grounded in DarGlobal and Wasalt data.",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS
allowed_origins = [
    settings.frontend_url,
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "https://estateiq-frontend-2qfo.onrender.com",
]
prod_url = os.getenv("PRODUCTION_FRONTEND_URL", "")
if prod_url:
    allowed_origins.append(prod_url)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "An unexpected error occurred. Please try again."},
    )


from app.api import health, chat, stats, sources, scrape  # noqa: E402
app.include_router(health.router)
app.include_router(chat.router)
app.include_router(stats.router)
app.include_router(sources.router)
app.include_router(scrape.router)


@app.get("/", tags=["System"])
async def root():
    return {"name": "EstateIQ API", "version": "1.0.0", "docs": "/docs", "health": "/health"}
