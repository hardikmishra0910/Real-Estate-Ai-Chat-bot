"""
Embedding function — uses ChromaDB's DefaultEmbeddingFunction.
This uses the onnx model bundled inside chromadb itself with no extra deps.
Falls back to a simple hash-based approach if that also fails.
"""

from functools import lru_cache
from app.core.logging import get_logger

logger = get_logger(__name__)


@lru_cache(maxsize=1)
def get_chroma_embedding_function():
    """Get the best available embedding function."""
    # Try 1: chromadb's built-in default (uses onnxruntime bundled with chromadb)
    try:
        from chromadb.utils.embedding_functions import DefaultEmbeddingFunction
        ef = DefaultEmbeddingFunction()
        # Warm up test
        test = ef(["test"])
        logger.info(f"Using DefaultEmbeddingFunction — dim={len(test[0])}")
        return ef
    except Exception as e:
        logger.warning(f"DefaultEmbeddingFunction failed: {e}")

    # Try 2: ONNXMiniLM
    try:
        from chromadb.utils.embedding_functions import ONNXMiniLM_L6_V2
        ef = ONNXMiniLM_L6_V2()
        test = ef(["test"])
        logger.info(f"Using ONNXMiniLM_L6_V2 — dim={len(test[0])}")
        return ef
    except Exception as e:
        logger.warning(f"ONNXMiniLM_L6_V2 failed: {e}")

    raise RuntimeError("No embedding function available. Check chromadb installation.")


def embed_texts(texts: list[str], model_name: str = "") -> list[list[float]]:
    ef = get_chroma_embedding_function()
    return [list(e) for e in ef(texts)]
