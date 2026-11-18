# Architecture Document

## System Overview

EstateIQ is a RAG (Retrieval-Augmented Generation) chatbot with a monorepo structure containing a Next.js frontend, FastAPI backend, and ChromaDB vector database.

## Component Diagram

```
Browser
  │
  ▼
Next.js Frontend (Port 3000)
  │  REST API calls to /api/*
  ▼
FastAPI Backend (Port 8000)
  ├── POST /api/chat
  │     ├── ChromaDB semantic_search()
  │     │     └── SentenceTransformer embeddings
  │     └── OpenRouter API (LLM)
  ├── GET  /health
  ├── GET  /api/stats
  ├── GET  /api/sources
  └── POST /api/scrape
        ├── DarGlobal scraper (requests + BS4)
        ├── Wasalt scraper   (requests + BS4)
        ├── LangChain text splitter (chunking)
        ├── SentenceTransformer (embedding)
        └── ChromaDB upsert
```

## RAG Pipeline Detail

```
User Question
    │
    ▼
embed_texts(question)        ← all-MiniLM-L6-v2
    │
    ▼
ChromaDB.query(              ← cosine similarity
  embedding,
  n_results=5,
  where=source_filter
)
    │
    ▼
Top-K chunks (content + metadata + score)
    │
    ▼
Build context block:
  [Source 1] Title
  URL: ...
  Content: ...
    │
    ▼
OpenRouter /chat/completions
  system: SYSTEM_PROMPT + context
  user:   question
    │
    ▼
Answer + source citations → frontend
```

## Data Flow

```
Scrape → Clean → Chunk → Embed → ChromaDB
              ↓
         data/raw/*.jsonl      (source documents)
         data/processed/chunks.jsonl  (chunks)
         data/chromadb/        (vector index)
```

## Security Considerations

- API key stored in `.env` only, never committed
- Docker secrets via env_file, not baked into images
- Input validation via Pydantic (max 2000 chars, non-blank)
- CORS restricted to known frontend origins
- No personal data collected from either source
- Robots.txt compliance verified before each scraping run
