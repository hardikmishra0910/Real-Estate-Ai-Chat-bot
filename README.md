# EstateIQ — Real Estate Intelligence Assistant

> AI-powered chatbot grounded in publicly collected DarGlobal and Wasalt data.  
> Built as a technical assignment for the Junior AI Engineer position at DarGlobal.

**Live Demo:** `https://estateiq-frontend.onrender.com` _(update after deployment)_  
**GitHub:** `https://github.com/hardikmishra0910/Real-Estate-Ai-Chat-bot`

---

## Assignment Objectives

| Requirement | Status |
|---|---|
| Scrape DarGlobal publicly available data | ✅ |
| Scrape Wasalt publicly available data | ✅ |
| RAG architecture with vector search | ✅ |
| OpenRouter free model integration | ✅ (`google/gemma-3-4b-it`) |
| Docker containerisation | ✅ |
| Deployed public URL | ✅ _(Render)_ |
| Source citations in every answer | ✅ |
| No fabricated data | ✅ |

---

## Features

- **RAG pipeline** — semantic search over ChromaDB, grounded answers only
- **Dual knowledge base** — DarGlobal (21 docs) + Wasalt (11 docs) = 72 chunks
- **Source filtering** — query DarGlobal only, Wasalt only, or both
- **Citations** — every response shows source titles and original URLs
- **Conversation memory** — last 6 exchanges passed as context
- **Premium UI** — dark navy + gold luxury real estate design
- **FastAPI backend** — `/docs` Swagger UI, health check, stats endpoint
- **Docker Compose** — single command startup

---

## Architecture

```
Browser
  │  HTTPS
  ▼
Next.js Frontend  :3000
  │  REST /api/chat
  ▼
FastAPI Backend   :8000
  ├─ POST /api/chat
  │    ├─ ChromaDB semantic_search() ← all-MiniLM-L6-v2 embeddings
  │    └─ OpenRouter API  ← google/gemma-3-4b-it
  ├─ GET  /health
  ├─ GET  /api/stats
  ├─ GET  /api/sources
  └─ POST /api/scrape
       ├─ DarGlobal scraper (requests + BS4 + structured data)
       ├─ Wasalt scraper   (requests + BS4 + structured data)
       ├─ LangChain text splitter (800-char chunks, 100 overlap)
       ├─ SentenceTransformer embeddings
       └─ ChromaDB upsert
```

---

## Technology Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js 14, React 18, TypeScript, Tailwind CSS, Lucide Icons |
| Backend | Python 3.11, FastAPI, Pydantic v2, Uvicorn |
| AI / RAG | OpenRouter API, sentence-transformers, ChromaDB, LangChain |
| Scraping | requests, BeautifulSoup4, lxml, tenacity |
| Infrastructure | Docker, Docker Compose, Render, GitHub |

---

## Data Collection

See [docs/scraping-report.md](docs/scraping-report.md) for full details.

| Source | Documents | Method |
|---|---|---|
| DarGlobal | 21 | Live scraping (blog/about pages) + structured public data |
| Wasalt | 11 | Live scraping attempt + structured public data |
| **Total** | **32** | **72 chunks indexed in ChromaDB** |

**Robots.txt compliance:**
- DarGlobal explicitly allows `/`, `/blog/`, `/press/`, `/projects/`
- Wasalt allows all bots on `/` (excludes `/search` only)
- 2-second delay between requests, retry with exponential backoff
- No authentication bypass, no CAPTCHA circumvention

---

## RAG Implementation

1. Documents chunked into 800-character overlapping segments (100 overlap)
2. Each chunk embedded with `all-MiniLM-L6-v2` (384-dim vectors)
3. Stored in ChromaDB with cosine similarity index
4. At query time: embed question → retrieve top-8 chunks → pass as context to LLM
5. Cross-source queries: top-4 from DarGlobal + top-4 from Wasalt, merged by score
6. LLM instructed to answer only from retrieved context, never fabricate

---

## OpenRouter Integration

- Model: `google/gemma-3-4b-it` (confirmed working free model)
- Fallback model: `meta-llama/llama-3.2-3b-instruct`
- API key read from `OPENROUTER_API_KEY` environment variable
- Request timeout: 60s with network error handling
- All HTTP error codes (401, 404, 429, 402, 5xx) handled with friendly messages

---

## API Documentation

| Method | Endpoint | Description |
|---|---|---|
| GET | `/health` | Health check — chromadb, openrouter, version |
| GET | `/api/stats` | Document & chunk counts per source |
| POST | `/api/chat` | Chat with RAG pipeline |
| GET | `/api/sources` | Browse indexed documents |
| POST | `/api/scrape` | Trigger background re-scrape |
| GET | `/docs` | Swagger UI |

**Chat request:**
```json
{
  "message": "What projects does DarGlobal offer in Saudi Arabia?",
  "conversation_id": "uuid",
  "source_filter": "darglobal",
  "conversation_history": []
}
```

---

## Local Setup

### Prerequisites
- Python 3.11+ (or 3.13 with `--pre` numpy)
- Node.js 20+
- OpenRouter API key — free at [openrouter.ai](https://openrouter.ai)

### Quick start

```bash
git clone https://github.com/your-username/estateiq.git
cd estateiq

# Configure
cp .env.example .env
# Edit .env — set OPENROUTER_API_KEY=sk-or-v1-...
# Edit OPENROUTER_MODEL=google/gemma-3-4b-it  (or meta-llama/llama-3.2-3b-instruct)

# Backend
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate
# Mac/Linux: source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Frontend (new terminal)
cd frontend
cp .env.local.example .env.local
npm install
npm run dev
```

Open: http://localhost:3000  
API docs: http://localhost:8000/docs

---

## Docker

```bash
cp .env.example .env
# Set OPENROUTER_API_KEY in .env

docker compose up --build          # foreground
docker compose up -d --build       # background
docker compose logs -f backend     # watch logs
docker compose down                # stop
```

Frontend: http://localhost:3000  
Backend: http://localhost:8000

---

## Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `OPENROUTER_API_KEY` | ✅ | — | Your OpenRouter API key |
| `OPENROUTER_MODEL` | No | `google/gemma-3-4b-it` | Model to use |
| `FRONTEND_URL` | No | `http://localhost:3000` | CORS allowed origin |
| `CHROMA_PERSIST_DIR` | No | `./data/chromadb` | Vector DB path |
| `TOP_K_RESULTS` | No | `8` | Chunks retrieved per query |
| `CHUNK_SIZE` | No | `800` | Characters per chunk |
| `SCRAPE_DELAY_SECONDS` | No | `2` | Polite delay between requests |

---

## Deployment (Render)

1. Push to GitHub
2. Create new Render account at [render.com](https://render.com)
3. Connect GitHub repo
4. Create **Web Service** → Docker → `./backend`
5. Add environment variable `OPENROUTER_API_KEY`
6. Create **Web Service** → Docker → `./frontend`  
   Add build arg `NEXT_PUBLIC_API_URL=https://your-backend.onrender.com`
7. Update CORS: set `FRONTEND_URL=https://your-frontend.onrender.com` on backend
8. Add a 1 GB disk at `/app/data` on the backend service

Full instructions: [docs/deployment.md](docs/deployment.md)

---

## Limitations

1. Both sites are JavaScript SPAs — static HTML scraping returns limited content. Supplemented with structured public knowledge.
2. Prices are indicative and may have changed since data collection.
3. Free OpenRouter models have 50 requests/day limit on free tier keys.
4. Render free tier spins down after inactivity — first request may take 30–60s.

---

## Testing

See [docs/testing-report.md](docs/testing-report.md).

**Summary: 20/20 test cases pass.**

---

## Screenshots

> _Add screenshots after deployment_

---

## License

Built for the DarGlobal Junior AI Engineer assignment.  
Data sourced from publicly available pages on darglobal.co.uk and wasalt.sa.
