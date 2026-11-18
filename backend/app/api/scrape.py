"""Scrape endpoint — trigger data collection and indexing."""

from fastapi import APIRouter, BackgroundTasks, HTTPException

from app.models.schemas import ScrapeRequest, ScrapeResponse
from app.services.ingestion_service import run_ingestion
from app.core.logging import get_logger

router = APIRouter()
logger = get_logger(__name__)

# Track if a scrape is already running
_scrape_running = False


@router.post("/api/scrape", response_model=ScrapeResponse, tags=["Data"])
async def trigger_scrape(request: ScrapeRequest, background_tasks: BackgroundTasks):
    """
    Trigger data collection from DarGlobal and/or Wasalt,
    followed by chunking and ChromaDB indexing.

    Set force_refresh=true to re-scrape even if cached data exists.
    """
    global _scrape_running

    if _scrape_running:
        raise HTTPException(
            status_code=409,
            detail="A scrape is already in progress. Please wait for it to complete.",
        )

    def _run():
        global _scrape_running
        _scrape_running = True
        try:
            stats = run_ingestion(
                sources=request.sources,
                force_refresh=request.force_refresh,
            )
            logger.info(f"[Scrape] Completed: {stats}")
        except Exception as e:
            logger.error(f"[Scrape] Failed: {e}", exc_info=True)
        finally:
            _scrape_running = False

    background_tasks.add_task(_run)

    return ScrapeResponse(
        status="started",
        message=(
            f"Scraping started for: {', '.join(request.sources)}. "
            "Check /api/stats for progress."
        ),
        stats={},
    )
