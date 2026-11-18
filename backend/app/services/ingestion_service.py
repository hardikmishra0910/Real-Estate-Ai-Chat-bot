"""Data ingestion service — scrape → chunk → embed → index."""

import json
from pathlib import Path
from datetime import datetime, timezone

from app.scraper.darglobal_scraper import DarGlobalScraper
from app.scraper.wasalt_scraper import WasaltScraper
from app.rag.chunker import chunk_documents
from app.rag.vectorstore import index_chunks, delete_collection, get_collection_stats
from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()

UNIFIED_COLLECTION = "estateiq_docs"
RAW_DATA_DIR = Path("./data/raw")
PROCESSED_DATA_DIR = Path("./data/processed")


def run_ingestion(
    sources: list[str] = ("darglobal", "wasalt"),
    force_refresh: bool = False,
) -> dict:
    """
    Full ingestion pipeline.
    Returns stats dict.
    """
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)

    all_documents = []
    scrape_stats = {}

    for source in sources:
        raw_path = RAW_DATA_DIR / f"{source}.jsonl"

        # Check if we can reuse cached data
        if raw_path.exists() and not force_refresh:
            logger.info(f"[{source}] Loading cached data from {raw_path}")
            docs = []
            with open(raw_path, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        docs.append(json.loads(line))
            scrape_stats[source] = {
                "documents": len(docs),
                "source": "cache",
            }
        else:
            logger.info(f"[{source}] Running live scrape...")
            if source == "darglobal":
                scraper = DarGlobalScraper(
                    delay=settings.scrape_delay_seconds,
                    max_pages=settings.max_pages_per_site,
                )
            else:
                scraper = WasaltScraper(
                    delay=settings.scrape_delay_seconds,
                    max_pages=settings.max_pages_per_site,
                )

            docs = scraper.scrape()
            scraper.save(docs, raw_path)
            scrape_stats[source] = {
                "documents": len(docs),
                "source": "live",
                "scraper_stats": scraper.stats,
                "failed_urls": len(scraper.failed_urls),
            }

        all_documents.extend(docs)

    logger.info(f"Total documents collected: {len(all_documents)}")

    # Chunk
    chunks = chunk_documents(
        all_documents,
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
    )

    # Save processed chunks
    chunks_path = PROCESSED_DATA_DIR / "chunks.jsonl"
    with open(chunks_path, "w", encoding="utf-8") as f:
        for chunk in chunks:
            f.write(json.dumps(chunk, ensure_ascii=False) + "\n")
    logger.info(f"Saved {len(chunks)} chunks to {chunks_path}")

    # Clear existing collection if force refresh
    if force_refresh:
        delete_collection(UNIFIED_COLLECTION, settings.chroma_persist_dir)

    # Index
    indexed = index_chunks(
        chunks,
        collection_name=UNIFIED_COLLECTION,
        persist_dir=settings.chroma_persist_dir,
        embedding_model=settings.embedding_model,
    )

    # Final stats
    collection_stats = get_collection_stats(settings.chroma_persist_dir)

    return {
        "status": "success",
        "total_documents": len(all_documents),
        "total_chunks": len(chunks),
        "indexed_chunks": indexed,
        "sources": scrape_stats,
        "collection": collection_stats.get(UNIFIED_COLLECTION, 0),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def load_existing_chunks() -> list[dict]:
    """Load previously processed chunks from disk."""
    chunks_path = PROCESSED_DATA_DIR / "chunks.jsonl"
    if not chunks_path.exists():
        return []
    chunks = []
    with open(chunks_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                chunks.append(json.loads(line))
    return chunks
