"""ChromaDB vector store management — compatible with chromadb >= 1.0."""

import chromadb
from pathlib import Path
from typing import Optional

from app.rag.embeddings import embed_texts
from app.core.logging import get_logger

logger = get_logger(__name__)

_chroma_client: Optional[chromadb.PersistentClient] = None


def get_chroma_client(persist_dir: str = "./data/chromadb") -> chromadb.PersistentClient:
    global _chroma_client
    if _chroma_client is None:
        Path(persist_dir).mkdir(parents=True, exist_ok=True)
        _chroma_client = chromadb.PersistentClient(path=persist_dir)
        logger.info(f"ChromaDB client initialised at: {persist_dir}")
    return _chroma_client


def _collection_names(client: chromadb.PersistentClient) -> list[str]:
    """Return collection names — handles both chromadb 0.x (str) and 1.x (Collection)."""
    cols = client.list_collections()
    result = []
    for c in cols:
        if isinstance(c, str):
            result.append(c)
        else:
            result.append(c.name)
    return result


def get_or_create_collection(
    client: chromadb.PersistentClient,
    name: str,
) -> chromadb.Collection:
    return client.get_or_create_collection(name=name)


def index_chunks(
    chunks: list[dict],
    collection_name: str,
    persist_dir: str = "./data/chromadb",
    embedding_model: str = "all-MiniLM-L6-v2",
    batch_size: int = 64,
) -> int:
    """Embed and store chunks in ChromaDB. Returns number of chunks indexed."""
    if not chunks:
        logger.warning("No chunks to index.")
        return 0

    client = get_chroma_client(persist_dir)
    collection = get_or_create_collection(client, collection_name)

    # Batch processing
    indexed = 0
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i : i + batch_size]
        texts = [c["content"] for c in batch]
        ids = [c["chunk_id"] for c in batch]

        embeddings = embed_texts(texts, embedding_model)

        metadatas = [
            {
                "parent_id": c["parent_id"],
                "source": c["source"],
                "source_url": c["source_url"],
                "title": c["title"],
                "doc_type": c["doc_type"],
                "location": c["location"],
                "chunk_index": c["chunk_index"],
                "total_chunks": c["total_chunks"],
                "scraped_at": c["scraped_at"],
            }
            for c in batch
        ]

        collection.upsert(
            ids=ids,
            embeddings=embeddings,
            documents=texts,
            metadatas=metadatas,
        )
        indexed += len(batch)
        logger.info(f"Indexed batch {i//batch_size + 1}: {indexed}/{len(chunks)} chunks")

    logger.info(f"Indexed {indexed} chunks into collection '{collection_name}'")
    return indexed


def semantic_search(
    query: str,
    collection_name: str,
    persist_dir: str = "./data/chromadb",
    embedding_model: str = "all-MiniLM-L6-v2",
    top_k: int = 5,
    source_filter: Optional[str] = None,
) -> list[dict]:
    """
    Search the vector store for chunks relevant to the query.
    source_filter: 'darglobal' | 'wasalt' | None (all)
    """
    client = get_chroma_client(persist_dir)

    # Check collection exists
    existing = _collection_names(client)
    if collection_name not in existing:
        logger.warning(f"Collection '{collection_name}' does not exist.")
        return []

    collection = client.get_collection(collection_name)

    if collection.count() == 0:
        return []

    query_embedding = embed_texts([query], embedding_model)[0]

    where_filter = None
    if source_filter and source_filter != "all":
        where_filter = {"source": {"$eq": source_filter}}

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=min(top_k, collection.count()),
        where=where_filter,
        include=["documents", "metadatas", "distances"],
    )

    hits = []
    if results and results.get("ids") and results["ids"][0]:
        for doc, meta, distance in zip(
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0],
        ):
            # Convert cosine distance to similarity score (0-1)
            score = max(0.0, 1.0 - distance)
            hits.append({
                "content": doc,
                "source": meta.get("source", ""),
                "source_url": meta.get("source_url", ""),
                "title": meta.get("title", ""),
                "doc_type": meta.get("doc_type", ""),
                "location": meta.get("location", ""),
                "relevance_score": round(score, 4),
            })

    return hits


def get_collection_stats(
    persist_dir: str = "./data/chromadb",
    collection_names: Optional[list[str]] = None,
) -> dict:
    """Return stats about indexed collections."""
    client = get_chroma_client(persist_dir)
    existing = _collection_names(client)

    stats = {}
    names = collection_names or existing
    for name in names:
        if name in existing:
            col = client.get_collection(name)
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
