"""EstateIQ FastAPI application entry point."""

import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import get_settings
from app.core.logging import setup_logging, get_logger
from app.api import health, chat, stats, sources, scrape

# Boot logging immediately
setup_logging()
logger = get_logger(__name__)
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: initialise ChromaDB and optionally auto-ingest data."""
    logger.info("╔══════════════════════════════════╗")
    logger.info("║     EstateIQ Backend Starting    ║")
    logger.info("╚══════════════════════════════════╝")
    logger.info(f"Environment : {settings.environment}")
    logger.info(f"Embedding   : {settings.embedding_model}")
    logger.info(f"Model       : {settings.openrouter_model}")
    logger.info(f"ChromaDB    : {settings.chroma_persist_dir}")

    # Ensure data directories exist
    Path(settings.chroma_persist_dir).mkdir(parents=True, exist_ok=True)
    Path("./data/raw").mkdir(parents=True, exist_ok=True)
    Path("./data/processed").mkdir(parents=True, exist_ok=True)

    # Auto-ingest if no data exists yet
    from app.rag.vectorstore import get_collection_stats
    stats_data = get_collection_stats(settings.chroma_persist_dir)
    total_chunks = sum(stats_data.values())

    if total_chunks == 0:
        logger.info("No data indexed. Running initial ingestion...")
        try:
            from app.services.ingestion_service import run_ingestion
            result = run_ingestion(sources=["darglobal", "wasalt"], force_refresh=True)
            logger.info(
                f"Ingestion complete: {result['total_documents']} docs, "
                f"{result['indexed_chunks']} chunks"
            )
        except Exception as e:
            logger.error(f"Auto-ingestion failed: {e}", exc_info=True)
            logger.warning("Server will start without data. Use POST /api/scrape to ingest.")
    else:
        logger.info(f"ChromaDB ready: {total_chunks} chunks already indexed.")

    yield

    logger.info("EstateIQ Backend shutting down.")


# ── App factory ───────────────────────────────────────────────────────────────

app = FastAPI(
    title="EstateIQ API",
    description=(
        "AI-powered real estate intelligence assistant. "
        "Answers questions grounded in DarGlobal and Wasalt data."
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── CORS ──────────────────────────────────────────────────────────────────────

allowed_origins = [
    settings.frontend_url,
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

# Allow production domains when set
if os.getenv("PRODUCTION_FRONTEND_URL"):
    allowed_origins.append(os.getenv("PRODUCTION_FRONTEND_URL"))

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# ── Global error handler ──────────────────────────────────────────────────────

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "An unexpected error occurred. Please try again."},
    )

# ── Routers ───────────────────────────────────────────────────────────────────

app.include_router(health.router)
app.include_router(chat.router)
app.include_router(stats.router)
app.include_router(sources.router)
app.include_router(scrape.router)


@app.get("/", tags=["System"])
async def root():
    return {
        "name": "EstateIQ API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
    }
