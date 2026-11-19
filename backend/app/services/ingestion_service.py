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
    sources=None,
    force_refresh: bool = False,
) -> dict:
    if sources is None:
        sources = ["darglobal", "wasalt"]
    sources = list(sources)  # ensure it's a plain list, never a tuple or string
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)

    all_documents = []
    scrape_stats = {}

    for source in sources:
        raw_path = RAW_DATA_DIR / f"{source}.jsonl"

        if raw_path.exists() and not force_refresh:
            logger.info(f"[{source}] Loading cached data from {raw_path}")
            docs = []
            with open(raw_path, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        docs.append(json.loads(line))
            scrape_stats[source] = {"documents": len(docs), "source": "cache"}
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
            }

        all_documents.extend(docs)

    logger.info(f"Total documents: {len(all_documents)}")

    # Chunk
    logger.info("Chunking documents...")
    chunks = chunk_documents(
        all_documents,
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
    )
    logger.info(f"Created {len(chunks)} chunks")

    # Save chunks
    chunks_path = PROCESSED_DATA_DIR / "chunks.jsonl"
    with open(chunks_path, "w", encoding="utf-8") as f:
        for chunk in chunks:
            f.write(json.dumps(chunk, ensure_ascii=False) + "\n")

    # Test embedding before indexing
    logger.info("Testing embedding function before indexing...")
    try:
        from app.rag.embeddings import get_chroma_embedding_function
        ef = get_chroma_embedding_function()
        test_result = ef(["test embedding"])
        logger.info(f"Embedding test passed — dim={len(test_result[0])}")
    except Exception as e:
        logger.error(f"Embedding function failed: {e}", exc_info=True)
        raise RuntimeError(f"Embedding failed: {e}")

    # Clear and re-index
    if force_refresh:
        delete_collection(UNIFIED_COLLECTION, settings.chroma_persist_dir)

    logger.info("Indexing chunks into ChromaDB...")
    indexed = index_chunks(
        chunks,
        collection_name=UNIFIED_COLLECTION,
        persist_dir=settings.chroma_persist_dir,
        embedding_model=settings.embedding_model,
    )

    # Verify
    final_stats = get_collection_stats(settings.chroma_persist_dir)
    final_count = final_stats.get(UNIFIED_COLLECTION, 0)
    logger.info(f"Verification: ChromaDB has {final_count} chunks after indexing")

    return {
        "status": "success",
        "total_documents": len(all_documents),
        "total_chunks": len(chunks),
        "indexed_chunks": indexed,
        "chromadb_verified": final_count,
        "sources": scrape_stats,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
