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
    """Trigger indexing — returns immediately, runs in background thread."""
    global _scrape_running
    if _scrape_running:
        return JSONResponse({"status": "already_running", "message": "Check /api/stats for progress."})

    def _run():
        global _scrape_running
        _scrape_running = True
        try:
            logger.info("=== Background index started ===")
            from app.rag.embeddings import get_chroma_embedding_function
            ef = get_chroma_embedding_function()
            test = ef(["test"])
            logger.info(f"Embedding OK dim={len(test[0])}")

            from app.services.ingestion_service import run_ingestion
            stats = run_ingestion(sources=["darglobal", "wasalt"], force_refresh=True)
            logger.info(f"=== Index complete: {stats.get('indexed_chunks', 0)} chunks ===")
        except Exception as e:
            logger.error(f"Index failed: {e}\n{traceback.format_exc()}")
        finally:
            _scrape_running = False

    import threading
    threading.Thread(target=_run, daemon=True).start()

    return JSONResponse({
        "status": "started",
        "message": "Indexing started in background. Check /api/stats in 3 minutes to see chunks > 0.",
        "stats_url": "https://estateiq-backend-ji7y.onrender.com/api/stats"
    })
