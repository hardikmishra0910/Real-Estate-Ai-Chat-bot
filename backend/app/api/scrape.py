"""Scrape + index endpoints."""

import traceback
import threading
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
            message=f"Indexed {stats['indexed_chunks']} chunks.",
            stats=stats,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        _scrape_running = False


@router.get("/api/index", tags=["Data"])
async def trigger_index_get():
    """Start background indexing."""
    global _scrape_running

    # Reset stuck flag
    _scrape_running = False

    def _run():
        global _scrape_running
        _scrape_running = True
        try:
            from app.services.ingestion_service import run_ingestion
            stats = run_ingestion(sources=["darglobal", "wasalt"], force_refresh=True)
            logger.info(f"INDEX DONE: {stats.get('indexed_chunks')} chunks, verified={stats.get('chromadb_verified')}")
        except Exception as e:
            logger.error(f"INDEX ERROR: {e}\n{traceback.format_exc()}")
        finally:
            _scrape_running = False

    threading.Thread(target=_run, daemon=True).start()
    return JSONResponse({"status": "started", "message": "Indexing started. Check /api/stats in 3 minutes."})


@router.get("/api/debug", tags=["Data"])
async def debug_step_by_step():
    """
    Test each step of the pipeline individually.
    Open in browser to diagnose exactly where indexing fails.
    """
    results = {}

    # Step 1: embedding
    try:
        from app.rag.embeddings import get_chroma_embedding_function
        ef = get_chroma_embedding_function()
        test = ef(["DarGlobal luxury real estate Saudi Arabia"])
        results["embedding"] = f"OK dim={len(test[0])} type={type(ef).__name__}"
    except Exception as e:
        results["embedding"] = f"FAILED: {e}"
        return JSONResponse(results)

    # Step 2: chromadb write
    try:
        import chromadb
        from app.core.config import get_settings
        settings = get_settings()
        client = chromadb.PersistentClient(path=settings.chroma_persist_dir)
        # delete test collection if exists
        try:
            client.delete_collection("debug_test")
        except Exception:
            pass
        col = client.create_collection("debug_test")
        ef2 = get_chroma_embedding_function()
        embs = ef2(["test document one", "test document two"])
        col.add(
            ids=["t1", "t2"],
            embeddings=embs,
            documents=["test document one", "test document two"],
            metadatas=[{"source": "test"}, {"source": "test"}],
        )
        count = col.count()
        client.delete_collection("debug_test")
        results["chromadb_write"] = f"OK wrote and read {count} docs"
    except Exception as e:
        results["chromadb_write"] = f"FAILED: {traceback.format_exc()}"
        return JSONResponse(results)

    # Step 3: load raw data
    try:
        import json
        from pathlib import Path
        raw = Path("./data/raw")
        dg = list((raw / "darglobal.jsonl").open()) if (raw / "darglobal.jsonl").exists() else []
        ws = list((raw / "wasalt.jsonl").open()) if (raw / "wasalt.jsonl").exists() else []
        results["raw_data"] = f"darglobal={len(dg)} wasalt={len(ws)} lines"
    except Exception as e:
        results["raw_data"] = f"FAILED: {e}"

    # Step 4: chunk
    try:
        from app.rag.chunker import chunk_documents
        docs = [{"id": "x1", "source": "darglobal", "source_url": "https://darglobal.co.uk",
                 "title": "Test", "content": "DarGlobal is a luxury real estate developer " * 20,
                 "doc_type": "company", "location": "UAE", "scraped_at": "2026-01-01"}]
        chunks = chunk_documents(docs, chunk_size=200, chunk_overlap=20)
        results["chunking"] = f"OK produced {len(chunks)} chunks"
    except Exception as e:
        results["chunking"] = f"FAILED: {e}"

    # Step 5: full index of 2 test chunks
    try:
        from app.rag.vectorstore import index_chunks, get_collection_stats, delete_collection
        from app.core.config import get_settings
        settings = get_settings()
        test_chunks = [
            {"chunk_id": "c1", "parent_id": "p1", "source": "darglobal",
             "source_url": "https://darglobal.co.uk", "title": "Test Doc",
             "doc_type": "company", "location": "UAE", "content": "DarGlobal luxury real estate",
             "chunk_index": 0, "total_chunks": 1, "scraped_at": "2026-01-01"},
        ]
        delete_collection("debug_index_test", settings.chroma_persist_dir)
        n = index_chunks(test_chunks, "debug_index_test", settings.chroma_persist_dir)
        stats = get_collection_stats(settings.chroma_persist_dir)
        delete_collection("debug_index_test", settings.chroma_persist_dir)
        results["index_test"] = f"OK indexed={n} stats={stats}"
    except Exception as e:
        results["index_test"] = f"FAILED: {traceback.format_exc()}"

    results["overall"] = "ALL STEPS PASSED" if all("FAILED" not in str(v) for v in results.values()) else "SOME STEPS FAILED"
    return JSONResponse(results)
