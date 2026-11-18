"""Application configuration loaded from environment variables."""

from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
import os


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # OpenRouter
    openrouter_api_key: str = ""
    openrouter_model: str = "google/gemma-3-4b-it"
    openrouter_base_url: str = "https://openrouter.ai/api/v1"

    # Backend
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000
    environment: str = "development"
    secret_key: str = "change_me_in_production"

    # CORS
    frontend_url: str = "http://localhost:3000"

    # ChromaDB
    chroma_persist_dir: str = "./data/chromadb"
    chroma_collection_darglobal: str = "darglobal_docs"
    chroma_collection_wasalt: str = "wasalt_docs"

    # Scraping
    scrape_delay_seconds: float = 2.0
    max_pages_per_site: int = 50

    # RAG
    embedding_model: str = "all-MiniLM-L6-v2"
    chunk_size: int = 800
    chunk_overlap: int = 100
    top_k_results: int = 5


@lru_cache()
def get_settings() -> Settings:
    return Settings()
