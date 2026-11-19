"""ChromaDB vector store — works with chromadb >= 0.4."""

import chromadb
from pathlib import Path
from typing import Optional
from app.core.logging import get_logger

logger = get_logger(__name__)
_client: Optional[chromadb.PersistentClient] = None


def get_client(persist_dir: str = "./data/chromadb") -> chromadb.PersistentClient:
    global _client
    if _client is None:
        Path(persist_dir).mkdir(parents=True, exist_ok=True)
        _client = chromadb.PersistentClient(path=persist_dir)
        logger.info(f"ChromaDB ready at: {persist_dir}")
    return _client


def _names(client) -> list[str]:
    return [c if isinstance(c, str) else c.name for c in client.list_collections()]


def index_chunks(chunks: list[dict], collection_name: str,
                 persist_dir: str = "./data/chromadb",
                 embedding_model: str = "", batch_size: int = 32) -> int:
    if not chunks:
        return 0

    from app.rag.embeddings import embed_texts

    client = get_client(persist_dir)
    # Delete and recreate to avoid stale data
    try:
        client.delete_collection(collection_name)
    except Exception:
        pass
    collection = client.create_collection(collection_name)

    indexed = 0
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i: i + batch_size]
        ids   = [c["chunk_id"] for c in batch]
        docs  = [c["content"]  for c in batch]
        metas = [{
            "source":      c["source"],
            "source_url":  c["source_url"],
            "title":       c["title"],
            "doc_type":    c["doc_type"],
            "location":    c["location"],
            "chunk_index": c["chunk_index"],
            "scraped_at":  c["scraped_at"],
        } for c in batch]

        embeddings = embed_texts(docs)
        collection.add(ids=ids, embeddings=embeddings, documents=docs, metadatas=metas)
        indexed += len(batch)
        logger.info(f"Indexed {indexed}/{len(chunks)}")

    logger.info(f"Done: {indexed} chunks in '{collection_name}'")
    return indexed


def semantic_search(query: str, collection_name: str,
                    persist_dir: str = "./data/chromadb",
                    embedding_model: str = "", top_k: int = 8,
                    source_filter: Optional[str] = None) -> list[dict]:
    from app.rag.embeddings import embed_texts

    client = get_client(persist_dir)
    if collection_name not in _names(client):
        return []

    collection = client.get_collection(collection_name)
    if collection.count() == 0:
        return []

    q_emb = embed_texts([query])[0]
    where = {"source": {"$eq": source_filter}} if source_filter else None

    res = collection.query(
        query_embeddings=[q_emb],
        n_results=min(top_k, collection.count()),
        where=where,
        include=["documents", "metadatas", "distances"],
    )

    hits = []
    if res and res["ids"] and res["ids"][0]:
        for doc, meta, dist in zip(res["documents"][0], res["metadatas"][0], res["distances"][0]):
            hits.append({
                "content": doc,
                "source": meta.get("source", ""),
                "source_url": meta.get("source_url", ""),
                "title": meta.get("title", ""),
                "doc_type": meta.get("doc_type", ""),
                "location": meta.get("location", ""),
                "relevance_score": round(max(0.0, 1.0 - float(dist)), 4),
            })
    return hits


def get_collection_stats(persist_dir: str = "./data/chromadb",
                         collection_names: Optional[list[str]] = None) -> dict:
    client = get_client(persist_dir)
    existing = _names(client)
    names = collection_names or existing
    return {n: (client.get_collection(n).count() if n in existing else 0) for n in names}


def delete_collection(name: str, persist_dir: str = "./data/chromadb") -> None:
    try:
        get_client(persist_dir).delete_collection(name)
        logger.info(f"Deleted: {name}")
    except Exception as e:
        logger.warning(f"Could not delete {name}: {e}")
