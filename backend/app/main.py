"""EstateIQ FastAPI — minimal stable startup."""

import os
import threading
import traceback
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
    import time
    time.sleep(10)
    try:
        from app.rag.vectorstore import get_collection_stats
        stats = get_collection_stats(settings.chroma_persist_dir)
        total = sum(stats.values())
        if total > 0:
            logger.info(f"ChromaDB has {total} chunks — no auto-ingest needed.")
            return
        # Data was pre-indexed in Docker image — if empty, something went wrong
        logger.warning("ChromaDB is empty after startup — data may not have been pre-indexed in Docker build.")
    except Exception as e:
        logger.error(f"Startup check error: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("EstateIQ starting...")
    Path(settings.chroma_persist_dir).mkdir(parents=True, exist_ok=True)
    Path("./data/raw").mkdir(parents=True, exist_ok=True)
    Path("./data/processed").mkdir(parents=True, exist_ok=True)
    threading.Thread(target=_background_ingest, daemon=True).start()
    yield
    logger.info("EstateIQ shutting down.")


app = FastAPI(
    title="EstateIQ API",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_handler(request: Request, exc: Exception):
    logger.error(f"Error: {exc}\n{traceback.format_exc()}")
    return JSONResponse(status_code=500, content={"detail": str(exc)})


# Import routers — each in try/except so one bad import doesn't kill the app
try:
    from app.api.health import router as health_router
    app.include_router(health_router)
except Exception as e:
    logger.error(f"health router failed: {e}")

try:
    from app.api.chat import router as chat_router
    app.include_router(chat_router)
except Exception as e:
    logger.error(f"chat router failed: {e}")

try:
    from app.api.stats import router as stats_router
    app.include_router(stats_router)
except Exception as e:
    logger.error(f"stats router failed: {e}")

try:
    from app.api.sources import router as sources_router
    app.include_router(sources_router)
except Exception as e:
    logger.error(f"sources router failed: {e}")

try:
    from app.api.scrape import router as scrape_router
    app.include_router(scrape_router)
except Exception as e:
    logger.error(f"scrape router failed: {e}")


@app.get("/")
async def root():
    return {"name": "EstateIQ API", "version": "1.0.0", "docs": "/docs"}
