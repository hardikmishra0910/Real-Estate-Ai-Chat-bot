"""Scrape + index endpoint."""

import traceback
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from app.models.schemas import ScrapeRequest, ScrapeResponse
from app.core.logging import get_logger

router = APIRouter()
logger = get_logger(__name__)

_scrape_running = False


@router.post("/api/scrape", response_model=ScrapeResponse, tags=["Data"])
async def trigger_scrape(request: ScrapeRequest):
    global _scrape_running
    if _scrape_running:
        raise HTTPException(status_code=409, detail="Scrape already running.")
    _scrape_running = True
    try:
        from app.services.ingestion_service import run_ingestion
        stats = run_ingestion(sources=list(request.sources), force_refresh=request.force_refresh)
        return ScrapeResponse(
            status="complete",
            message=f"Indexed {stats['indexed_chunks']} chunks from {stats['total_documents']} docs.",
            stats=stats,
        )
    except Exception as e:
        logger.error(f"Scrape failed: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        _scrape_running = False


@router.get("/api/index", tags=["Data"])
async def trigger_index_get():
    """GET endpoint — open in browser to trigger full re-index."""
    global _scrape_running
    if _scrape_running:
        return JSONResponse({"status": "already_running"})

    _scrape_running = True
    try:
        logger.info("=== /api/index triggered ===")

        # Step 1: test embedding
        logger.info("Step 1: Testing embedding...")
        from app.rag.embeddings import get_chroma_embedding_function
        ef = get_chroma_embedding_function()
        test = ef(["DarGlobal real estate"])
        dim = len(test[0])
        logger.info(f"Embedding OK — dim={dim}")

        # Step 2: run ingestion
        logger.info("Step 2: Running ingestion...")
        from app.services.ingestion_service import run_ingestion
        stats = run_ingestion(sources=["darglobal", "wasalt"], force_refresh=True)
        logger.info(f"Ingestion result: {stats}")

        return JSONResponse({
            "status": "complete",
            "total_documents": stats["total_documents"],
            "total_chunks": stats["total_chunks"],
            "indexed_chunks": stats["indexed_chunks"],
            "chromadb_verified": stats.get("chromadb_verified", 0),
            "embedding_dim": dim,
            "message": "Data indexed successfully. Chat is ready.",
        })
    except Exception as e:
        tb = traceback.format_exc()
        logger.error(f"Index failed:\n{tb}")
        return JSONResponse({"status": "error", "message": str(e), "traceback": tb}, status_code=500)
    finally:
        _scrape_running = False
