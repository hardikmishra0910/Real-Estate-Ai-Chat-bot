# Final Submission Email

---

**Subject:** Junior AI Engineer Assignment — EstateIQ Real Estate Intelligence Assistant

---

Dear DarGlobal Hiring Team,

Please find below my completed submission for the Junior AI Engineer — Applied AI technical assignment.

---

## Project: EstateIQ — Real Estate Intelligence Assistant

**GitHub Repository:** https://github.com/hardikmishra0910/Real-Estate-Ai-Chat-bot  
**Live Demo:** https://estateiq-frontend.onrender.com  
**Backend API Docs:** https://estateiq-backend.onrender.com/docs  
**Backend Health:** https://estateiq-backend.onrender.com/health  

---

## What Was Built

EstateIQ is a production-quality RAG (Retrieval-Augmented Generation) chatbot that answers questions about DarGlobal luxury real estate projects and Wasalt Saudi Arabian property listings. Every answer is strictly grounded in collected public data — the system never fabricates prices, locations, or project details.

---

## Assignment Requirements — Completion Status

| Requirement | Status | Detail |
|---|---|---|
| Scrape DarGlobal | ✅ | 21 documents (live scraping + structured public data) |
| Scrape Wasalt | ✅ | 11 documents (live attempt + structured public data) |
| Free AI model via OpenRouter | ✅ | `google/gemma-3-4b-it` (confirmed working) |
| RAG architecture | ✅ | ChromaDB + all-MiniLM-L6-v2 embeddings, 72 chunks |
| Docker containerisation | ✅ | Docker Compose with backend + frontend services |
| Public deployment | ✅ | Render.com |
| Source citations | ✅ | Every response includes title + URL |
| No data fabrication | ✅ | Tested and verified |
| README + documentation | ✅ | Architecture, scraping, testing reports |
| robots.txt compliance | ✅ | Verified before scraping both sites |

---

## Technology Stack

- **Frontend:** Next.js 14, React 18, TypeScript, Tailwind CSS, Lucide Icons
- **Backend:** Python 3.11, FastAPI, Pydantic v2
- **AI/RAG:** OpenRouter API, sentence-transformers, ChromaDB, LangChain
- **Scraping:** requests, BeautifulSoup4, tenacity (retry + rate limiting)
- **Infrastructure:** Docker Compose, GitHub, Render

---

## Key Design Decisions

1. **Robots.txt first** — Checked both sites' robots.txt before writing a single scraping line
2. **Structured data supplement** — Both sites are JavaScript SPAs; augmented live scraping with structured public knowledge to ensure the chatbot has useful data
3. **Dual-source retrieval** — Cross-source queries retrieve top-4 from each source independently, then merge by relevance score
4. **Strict grounding** — System prompt instructs the LLM to cite only what appears in retrieved context; hallucination tests verified

---

## Testing

20 test cases executed — all pass. Full report at `docs/testing-report.md` in the repository.

---

## Running Locally

```bash
git clone https://github.com/hardikmishra0910/Real-Estate-Ai-Chat-bot.git
cd Real-Estate-Ai-Chat-bot
cp .env.example .env
# Add OPENROUTER_API_KEY to .env
# Set OPENROUTER_MODEL=google/gemma-3-4b-it

# Docker (recommended)
docker compose up --build

# Or manual:
cd backend && python -m venv .venv && .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --port 8000

cd frontend && npm install && npm run dev
```

---

Thank you for the opportunity. I look forward to discussing the implementation.

Best regards,  
Hardik Mishra
