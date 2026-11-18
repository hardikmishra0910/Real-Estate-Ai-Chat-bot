"""Pydantic schemas for API request/response models."""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Literal
from datetime import datetime
import uuid


# ── Chat ──────────────────────────────────────────────────────────────────────

class ChatMessage(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)
    conversation_id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()))
    source_filter: Literal["all", "darglobal", "wasalt"] = "all"
    conversation_history: List[ChatMessage] = Field(default_factory=list)

    @field_validator("message")
    @classmethod
    def message_not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Message cannot be blank.")
        return v.strip()


class SourceCitation(BaseModel):
    source: str                        # "darglobal" | "wasalt"
    title: str
    url: str
    excerpt: str
    relevance_score: Optional[float] = None


class ChatResponse(BaseModel):
    answer: str
    conversation_id: str
    sources: List[SourceCitation] = Field(default_factory=list)
    model_used: str = ""
    tokens_used: Optional[int] = None
    retrieved_chunks: int = 0


# ── Stats ──────────────────────────────────────────────────────────────────────

class SourceStats(BaseModel):
    source: str
    document_count: int
    chunk_count: int
    last_scraped: Optional[str] = None


class StatsResponse(BaseModel):
    total_documents: int
    total_chunks: int
    sources: List[SourceStats]
    chromadb_status: str
    embedding_model: str


# ── Sources ────────────────────────────────────────────────────────────────────

class SourceDocument(BaseModel):
    id: str
    source: str
    title: str
    url: str
    content_preview: str
    doc_type: str
    scraped_at: str


class SourcesResponse(BaseModel):
    documents: List[SourceDocument]
    total: int
    source_filter: str


# ── Scrape ─────────────────────────────────────────────────────────────────────

class ScrapeRequest(BaseModel):
    sources: List[Literal["darglobal", "wasalt"]] = ["darglobal", "wasalt"]
    force_refresh: bool = False


class ScrapeResponse(BaseModel):
    status: str
    message: str
    stats: dict


# ── Health ─────────────────────────────────────────────────────────────────────

class HealthResponse(BaseModel):
    status: str
    version: str
    environment: str
    chromadb: str
    openrouter: str
    timestamp: str
