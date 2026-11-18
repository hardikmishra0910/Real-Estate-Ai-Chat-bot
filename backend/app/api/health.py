"""Health check endpoint."""

from fastapi import APIRouter
from datetime import datetime, timezone

from app.models.schemas import HealthResponse
from app.core.config import get_settings
from app.rag.vectorstore import get_chroma_client, get_collection_stats

router = APIRouter()
settings = get_settings()


@router.get("/health", response_model=HealthResponse, tags=["System"])
async def health_check():
    """Check API health, ChromaDB connectivity, and OpenRouter key status."""
    # ChromaDB status
    try:
        client = get_chroma_client(settings.chroma_persist_dir)
        client.list_collections()
        chroma_status = "ok"
    except Exception as e:
        chroma_status = f"error: {str(e)[:60]}"

    # OpenRouter key status (presence only, never expose the key)
    openrouter_status = "configured" if settings.openrouter_api_key else "missing"

    return HealthResponse(
        status="ok",
        version="1.0.0",
        environment=settings.environment,
        chromadb=chroma_status,
        openrouter=openrouter_status,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )
