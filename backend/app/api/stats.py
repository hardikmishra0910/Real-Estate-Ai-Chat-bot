"""Stats endpoint — data collection and indexing statistics."""

import json
from pathlib import Path
from fastapi import APIRouter

from app.models.schemas import StatsResponse, SourceStats
from app.rag.vectorstore import get_collection_stats
from app.core.config import get_settings

router = APIRouter()
settings = get_settings()

RAW_DATA_DIR = Path("./data/raw")


@router.get("/api/stats", response_model=StatsResponse, tags=["Data"])
async def get_stats():
    """Return statistics about indexed documents and ChromaDB collections."""
    # Collection stats
    col_stats = get_collection_stats(settings.chroma_persist_dir)
    total_chunks = sum(col_stats.values())

    # Document counts from raw data files
    source_stats = []
    total_docs = 0

    for source_name in ["darglobal", "wasalt"]:
        raw_path = RAW_DATA_DIR / f"{source_name}.jsonl"
        doc_count = 0
        last_scraped = None

        if raw_path.exists():
            with open(raw_path, encoding="utf-8") as f:
                docs = [json.loads(line) for line in f if line.strip()]
            doc_count = len(docs)
            if docs:
                scraped_dates = [d.get("scraped_at", "") for d in docs if d.get("scraped_at")]
                if scraped_dates:
                    last_scraped = max(scraped_dates)

        total_docs += doc_count
        source_stats.append(
            SourceStats(
                source=source_name,
                document_count=doc_count,
                chunk_count=col_stats.get("estateiq_docs", 0) if doc_count else 0,
                last_scraped=last_scraped,
            )
        )

    return StatsResponse(
        total_documents=total_docs,
        total_chunks=total_chunks,
        sources=source_stats,
        chromadb_status="ok" if total_chunks > 0 else "empty",
        embedding_model=settings.embedding_model,
    )
