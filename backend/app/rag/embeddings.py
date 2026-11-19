"""
Lightweight embedding using chromadb's built-in sentence transformer.
Falls back to keyword-based embedding if all else fails.
"""

from functools import lru_cache
from app.core.logging import get_logger

logger = get_logger(__name__)


@lru_cache(maxsize=1)
def get_chroma_embedding_function():
    """Get chromadb embedding function — tries multiple options."""

    # Option 1: chromadb default (uses its own bundled model)
    try:
        from chromadb.utils.embedding_functions import DefaultEmbeddingFunction
        ef = DefaultEmbeddingFunction()
        test = ef(["warmup"])
        logger.info(f"DefaultEmbeddingFunction OK — dim={len(test[0])}")
        return ef
    except Exception as e:
        logger.warning(f"DefaultEmbeddingFunction failed: {e}")

    # Option 2: sentence transformers if installed
    try:
        from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
        ef = SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
        test = ef(["warmup"])
        logger.info(f"SentenceTransformerEmbeddingFunction OK — dim={len(test[0])}")
        return ef
    except Exception as e:
        logger.warning(f"SentenceTransformerEmbeddingFunction failed: {e}")

    # Option 3: simple keyword embedding (always works, no deps)
    logger.warning("Using SimpleKeywordEmbeddingFunction fallback")
    return SimpleKeywordEmbeddingFunction()


class SimpleKeywordEmbeddingFunction:
    """
    Deterministic keyword-based embedding.
    Uses character n-gram hashing to 384 dimensions.
    No external dependencies. Works anywhere.
    """
    DIM = 384

    def __call__(self, input: list[str]) -> list[list[float]]:
        import hashlib
        import math
        results = []
        for text in input:
            vec = [0.0] * self.DIM
            text_lower = text.lower()
            # Character trigrams
            for i in range(len(text_lower) - 2):
                trigram = text_lower[i:i+3]
                h = int(hashlib.md5(trigram.encode()).hexdigest(), 16)
                idx = h % self.DIM
                vec[idx] += 1.0
            # Word unigrams
            for word in text_lower.split():
                h = int(hashlib.md5(word.encode()).hexdigest(), 16)
                idx = h % self.DIM
                vec[idx] += 2.0
            # Normalize
            magnitude = math.sqrt(sum(x * x for x in vec)) or 1.0
            vec = [x / magnitude for x in vec]
            results.append(vec)
        return results


def embed_texts(texts: list[str], model_name: str = "") -> list[list[float]]:
    ef = get_chroma_embedding_function()
    return [list(e) for e in ef(texts)]
