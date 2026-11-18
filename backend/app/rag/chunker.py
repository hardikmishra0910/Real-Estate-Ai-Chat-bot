"""Text chunking for RAG pipeline."""

from langchain_text_splitters import RecursiveCharacterTextSplitter
from app.core.logging import get_logger

logger = get_logger(__name__)


def chunk_documents(
    documents: list[dict],
    chunk_size: int = 800,
    chunk_overlap: int = 100,
) -> list[dict]:
    """
    Split documents into overlapping chunks suitable for embedding.
    Each chunk inherits metadata from the parent document.
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ". ", " ", ""],
        length_function=len,
    )

    chunks = []
    for doc in documents:
        content = doc.get("content", "")
        if not content or len(content.strip()) < 50:
            continue

        texts = splitter.split_text(content)
        for i, text in enumerate(texts):
            if len(text.strip()) < 30:
                continue
            chunk = {
                "chunk_id": f"{doc['id']}_{i}",
                "parent_id": doc["id"],
                "source": doc["source"],
                "source_url": doc["source_url"],
                "title": doc["title"],
                "doc_type": doc.get("doc_type", "general"),
                "location": doc.get("location", ""),
                "content": text,
                "chunk_index": i,
                "total_chunks": len(texts),
                "scraped_at": doc.get("scraped_at", ""),
            }
            chunks.append(chunk)

    logger.info(f"Chunked {len(documents)} documents → {len(chunks)} chunks")
    return chunks
