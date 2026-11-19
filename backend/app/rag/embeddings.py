"""Embedding function — pure Python fallback, zero external deps."""

from functools import lru_cache
from app.core.logging import get_logger

logger = get_logger(__name__)


@lru_cache(maxsize=1)
def get_chroma_embedding_function():
    # Try chromadb's built-in first
    try:
        from chromadb.utils.embedding_functions import DefaultEmbeddingFunction
        ef = DefaultEmbeddingFunction()
        test = ef(["warmup"])
        logger.info(f"DefaultEmbeddingFunction OK — dim={len(test[0])}")
        return ef
    except Exception as e:
        logger.warning(f"DefaultEmbeddingFunction failed: {e}")

    # Pure Python fallback — always works
    logger.warning("Using pure-Python keyword embedding fallback")
    return _KeywordEF()


class _KeywordEF:
    """Zero-dependency keyword hash embedding, dim=384."""
    DIM = 384

    def __call__(self, input):
        import hashlib, math
        out = []
        for text in input:
            v = [0.0] * self.DIM
            t = text.lower()
            for i in range(len(t) - 2):
                h = int(hashlib.md5(t[i:i+3].encode()).hexdigest(), 16)
                v[h % self.DIM] += 1.0
            for w in t.split():
                h = int(hashlib.md5(w.encode()).hexdigest(), 16)
                v[h % self.DIM] += 2.0
            mag = math.sqrt(sum(x*x for x in v)) or 1.0
            out.append([x/mag for x in v])
        return out


def embed_texts(texts, model_name=""):
    return get_chroma_embedding_function()(texts)
