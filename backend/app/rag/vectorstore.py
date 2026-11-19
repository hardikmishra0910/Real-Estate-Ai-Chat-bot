"""ChromaDB vector store — works with chromadb 0.5.x and 1.x."""

import chromadb
from pathlib import Path
from typing import Optional

from app.core.logging import get_logger

logger = get_logger(__name__)

_chroma_client: Optional[chromadb.PersistentClient] = None


def get_chroma_client(persist_dir: str = "./data/chromadb") -> chromadb.PersistentClient:
    global _chroma_client
    if _chroma_client is None:
        Path(persist_dir).mkdir(parents=True, exist_ok=True)
        _chroma_client = chromadb.PersistentClient(path=persist_dir)
        logger.info(f"ChromaDB initialised at: {persist_dir}")
    return _chroma_client


def _collection_names(client) -> list[str]:
    cols = client.list_collections()
    return [c if isinstance(c, str) else c.name for c in cols]


def index_chunks(
    chunks: list[dict],
    collection_name: str,
    persist_dir: str = "./data/chromadb",
    embedding_model: str = "",
    batch_size: int = 32,
) -> int:
    if not chunks:
        logger.warning("No chunks to index.")
        return 0

    from app.rag.embeddings import get_chroma_embedding_function
    ef = get_chroma_embedding_function()

    client = get_chroma_client(persist_dir)
    collection = client.get_or_create_collection(
        name=collection_name,
        embedding_function=ef,
    )

    indexed = 0
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i: i + batch_size]
        ids       = [c["chunk_id"] for c in batch]
        documents = [c["content"]  for c in batch]
        metadatas = [
            {
                "parent_id":   c["parent_id"],
                "source":      c["source"],
                "source_url":  c["source_url"],
                "title":       c["title"],
                "doc_type":    c["doc_type"],
                "location":    c["location"],
                "chunk_index": c["chunk_index"],
                "total_chunks":c["total_chunks"],
                "scraped_at":  c["scraped_at"],
            }
            for c in batch
        ]
        collection.upsert(ids=ids, documents=documents, metadatas=metadatas)
        indexed += len(batch)
        logger.info(f"Indexed {indexed}/{len(chunks)} chunks")

    logger.info(f"Total indexed: {indexed} into '{collection_name}'")
    return indexed


def semantic_search(
    query: str,
    collection_name: str,
    persist_dir: str = "./data/chromadb",
    embedding_model: str = "",
    top_k: int = 8,
    source_filter: Optional[str] = None,
) -> list[dict]:
    from app.rag.embeddings import get_chroma_embedding_function
    ef = get_chroma_embedding_function()

    client = get_chroma_client(persist_dir)
    if collection_name not in _collection_names(client):
        logger.warning(f"Collection '{collection_name}' not found.")
        return []

    collection = client.get_collection(collection_name, embedding_function=ef)
    count = collection.count()
    if count == 0:
        return []

    where = {"source": {"$eq": source_filter}} if source_filter else None

    results = collection.query(
        query_texts=[query],
        n_results=min(top_k, count),
        where=where,
        include=["documents", "metadatas", "distances"],
    )

    hits = []
    if results and results.get("ids") and results["ids"][0]:
        for doc, meta, dist in zip(
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0],
        ):
            score = max(0.0, 1.0 - float(dist))
            hits.append({
                "content":        doc,
                "source":         meta.get("source", ""),
                "source_url":     meta.get("source_url", ""),
                "title":          meta.get("title", ""),
                "doc_type":       meta.get("doc_type", ""),
                "location":       meta.get("location", ""),
                "relevance_score": round(score, 4),
            })
    return hits


def get_collection_stats(
    persist_dir: str = "./data/chromadb",
    collection_names: Optional[list[str]] = None,
) -> dict:
    from app.rag.embeddings import get_chroma_embedding_function
    ef = get_chroma_embedding_function()
    client = get_chroma_client(persist_dir)
    existing = _collection_names(client)
    names = collection_names or existing
    stats = {}
    for name in names:
        if name in existing:
            col = client.get_collection(name, embedding_function=ef)
            stats[name] = col.count()
        else:
            stats[name] = 0
    return stats


def delete_collection(name: str, persist_dir: str = "./data/chromadb") -> None:
    client = get_chroma_client(persist_dir)
    try:
        client.delete_collection(name)
        logger.info(f"Deleted collection: {name}")
    except Exception as e:
        logger.warning(f"Could not delete collection {name}: {e}")
