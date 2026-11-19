"""Scrape + index endpoint."""

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from app.models.schemas import ScrapeRequest, ScrapeResponse
from app.core.logging import get_logger

router = APIRouter()
logger = get_logger(__name__)

_scrape_running = False


@router.post("/api/scrape", response_model=ScrapeResponse, tags=["Data"])
async def trigger_scrape(request: ScrapeRequest):
    """
    Scrape and index data synchronously.
    Returns when complete so you can see the result immediately.
    """
    global _scrape_running
    if _scrape_running:
        raise HTTPException(status_code=409, detail="Scrape already running.")

    _scrape_running = True
    try:
        from app.services.ingestion_service import run_ingestion
        stats = run_ingestion(
            sources=request.sources,
            force_refresh=request.force_refresh,
        )
        return ScrapeResponse(
            status="complete",
            message=f"Indexed {stats['indexed_chunks']} chunks from {stats['total_documents']} documents.",
            stats=stats,
        )
    except Exception as e:
        logger.error(f"Scrape failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        _scrape_running = False


@router.get("/api/index", tags=["Data"])
async def trigger_index_get():
    """
    GET endpoint to trigger indexing — open in browser to index data.
    Runs synchronously and returns when complete.
    """
    global _scrape_running
    if _scrape_running:
        return JSONResponse({"status": "already_running", "message": "Scrape already in progress."})

    _scrape_running = True
    try:
        from app.services.ingestion_service import run_ingestion
        from app.rag.embeddings import get_chroma_embedding_function
        from app.core.config import get_settings
        settings = get_settings()

        # Test embedding first
        logger.info("Testing embedding function...")
        ef = get_chroma_embedding_function()
        test = ef(["DarGlobal luxury real estate"])
        logger.info(f"Embedding test OK — dim={len(test[0])}")

        logger.info("Running ingestion...")
        stats = run_ingestion(sources=["darglobal", "wasalt"], force_refresh=True)

        return JSONResponse({
            "status": "complete",
            "total_documents": stats["total_documents"],
            "total_chunks": stats["total_chunks"],
            "indexed_chunks": stats["indexed_chunks"],
            "embedding_dim": len(test[0]),
            "message": "Data indexed successfully. Chat is ready.",
        })
    except Exception as e:
        logger.error(f"Index failed: {e}", exc_info=True)
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)
    finally:
        _scrape_running = False
