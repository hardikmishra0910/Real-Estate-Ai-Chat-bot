"""
Embedding model — uses ChromaDB's built-in ONNX embedding function.
Memory footprint: ~100MB (vs ~1.5GB for sentence-transformers + torch).
Compatible with chromadb >= 0.4.x and 1.x.
"""

from functools import lru_cache
from app.core.logging import get_logger

logger = get_logger(__name__)


@lru_cache(maxsize=1)
def get_chroma_embedding_function():
    """Return ChromaDB's ONNX-based embedding function."""
    try:
        from chromadb.utils.embedding_functions import ONNXMiniLM_L6_V2
        logger.info("Loading ONNXMiniLM_L6_V2 embedding function")
        ef = ONNXMiniLM_L6_V2()
        logger.info("Embedding function ready")
        return ef
    except Exception as e:
        logger.warning(f"ONNXMiniLM_L6_V2 failed ({e}), trying DefaultEmbeddingFunction")
        try:
            from chromadb.utils.embedding_functions import DefaultEmbeddingFunction
            return DefaultEmbeddingFunction()
        except Exception as e2:
            logger.error(f"All embedding functions failed: {e2}")
            raise


def embed_texts(texts: list[str], model_name: str = "") -> list[list[float]]:
    """Embed texts using ChromaDB's ONNX function."""
    ef = get_chroma_embedding_function()
    results = ef(texts)
    return [list(e) for e in results]
