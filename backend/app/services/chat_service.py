"""Chat service — orchestrates RAG retrieval + LLM generation."""

from app.rag.vectorstore import semantic_search
from app.services.openrouter import OpenRouterClient, OpenRouterError
from app.models.schemas import ChatRequest, ChatResponse, SourceCitation
from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()

UNIFIED_COLLECTION = "estateiq_docs"


class ChatService:
    def __init__(self):
        self.openrouter = OpenRouterClient()

    def _retrieve(self, query: str, source_filter: str | None) -> list[dict]:
        """
        Retrieve relevant chunks. When source_filter is None (all sources),
        fetch top-K from each source individually then merge by score so both
        DarGlobal and Wasalt are represented in cross-source queries.
        """
        top_k = settings.top_k_results

        if source_filter and source_filter != "all":
            return semantic_search(
                query=query,
                collection_name=UNIFIED_COLLECTION,
                persist_dir=settings.chroma_persist_dir,
                embedding_model=settings.embedding_model,
                top_k=top_k,
                source_filter=source_filter,
            )

        # For "all": fetch from each source, take top half each, merge & sort
        half_k = max(3, top_k // 2)
        dg_chunks = semantic_search(
            query=query,
            collection_name=UNIFIED_COLLECTION,
            persist_dir=settings.chroma_persist_dir,
            embedding_model=settings.embedding_model,
            top_k=half_k,
            source_filter="darglobal",
        )
        ws_chunks = semantic_search(
            query=query,
            collection_name=UNIFIED_COLLECTION,
            persist_dir=settings.chroma_persist_dir,
            embedding_model=settings.embedding_model,
            top_k=half_k,
            source_filter="wasalt",
        )
        # Merge and sort by relevance score descending
        combined = dg_chunks + ws_chunks
        combined.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)
        return combined[:top_k]

    async def process_chat(self, request: ChatRequest) -> ChatResponse:
        source_filter = (
            request.source_filter if request.source_filter != "all" else None
        )

        chunks = self._retrieve(request.message, source_filter)

        logger.info(
            f"[Chat] Retrieved {len(chunks)} chunks "
            f"(sources: {list({c.get('source') for c in chunks})}) "
            f"for: '{request.message[:60]}'"
        )

        history = [
            {"role": m.role, "content": m.content}
            for m in request.conversation_history
        ]

        try:
            result = await self.openrouter.chat(
                user_message=request.message,
                context_chunks=chunks,
                conversation_history=history,
            )
        except OpenRouterError as e:
            return ChatResponse(
                answer=str(e),
                conversation_id=request.conversation_id,
                sources=[],
                model_used="error",
                retrieved_chunks=len(chunks),
            )

        # Deduplicated source citations
        seen_urls: set[str] = set()
        citations: list[SourceCitation] = []
        for chunk in chunks:
            url = chunk.get("source_url", "")
            if url in seen_urls:
                continue
            seen_urls.add(url)
            citations.append(
                SourceCitation(
                    source=chunk.get("source", ""),
                    title=chunk.get("title", ""),
                    url=url,
                    excerpt=chunk.get("content", "")[:200] + "…",
                    relevance_score=chunk.get("relevance_score"),
                )
            )

        return ChatResponse(
            answer=result["answer"],
            conversation_id=request.conversation_id,
            sources=citations,
            model_used=result.get("model", ""),
            tokens_used=result.get("tokens"),
            retrieved_chunks=len(chunks),
        )
