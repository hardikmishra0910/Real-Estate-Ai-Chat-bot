"""Chat endpoint — RAG-powered AI responses."""

from fastapi import APIRouter, HTTPException

from app.models.schemas import ChatRequest, ChatResponse
from app.services.chat_service import ChatService
from app.core.logging import get_logger

router = APIRouter()
logger = get_logger(__name__)

chat_service = ChatService()


@router.post("/api/chat", response_model=ChatResponse, tags=["Chat"])
async def chat(request: ChatRequest):
    """
    Send a message to EstateIQ and receive an AI-generated answer
    grounded in retrieved DarGlobal and Wasalt data.
    """
    logger.info(
        f"[/api/chat] source={request.source_filter} | "
        f"msg='{request.message[:80]}'"
    )

    try:
        response = await chat_service.process_chat(request)
        return response
    except Exception as e:
        logger.error(f"[/api/chat] Unexpected error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="An internal error occurred while processing your request.",
        )
