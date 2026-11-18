"""Sources endpoint — browse indexed documents."""

import json
from pathlib import Path
from fastapi import APIRouter, Query

from app.models.schemas import SourcesResponse, SourceDocument

router = APIRouter()

RAW_DATA_DIR = Path("./data/raw")


@router.get("/api/sources", response_model=SourcesResponse, tags=["Data"])
async def get_sources(
    source: str = Query("all", description="Filter: 'all', 'darglobal', or 'wasalt'"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    """Browse the indexed source documents."""
    all_docs = []

    for source_name in ["darglobal", "wasalt"]:
        if source != "all" and source_name != source:
            continue
        raw_path = RAW_DATA_DIR / f"{source_name}.jsonl"
        if not raw_path.exists():
            continue
        with open(raw_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    all_docs.append(json.loads(line))

    total = len(all_docs)
    page = all_docs[offset : offset + limit]

    documents = [
        SourceDocument(
            id=doc.get("id", ""),
            source=doc.get("source", ""),
            title=doc.get("title", ""),
            url=doc.get("source_url", ""),
            content_preview=doc.get("content", "")[:300],
            doc_type=doc.get("doc_type", "general"),
            scraped_at=doc.get("scraped_at", ""),
        )
        for doc in page
    ]

    return SourcesResponse(
        documents=documents,
        total=total,
        source_filter=source,
    )
