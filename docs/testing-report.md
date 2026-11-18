# Testing Report — EstateIQ

**Date:** 2026-11-18  
**Environment:** Local (Python 3.13, Node 20, Windows)  
**Backend:** FastAPI + ChromaDB (72 chunks) + google/gemma-3-4b-it  
**Frontend:** Next.js 14 dev server

---

## Test Results

| # | Test Case | Expected | Actual | Status |
|---|---|---|---|---|
| 1 | DarGlobal company info | Description, CEO, LSE listing | Returns Ziad El Chaar, LSE ticker DAR, USD 19B pipeline | ✅ PASS |
| 2 | DarGlobal project info | Lists projects with names and locations | Returns AIDA Oman, Trump Tower Jeddah, Trump Plaza Jeddah, DaVinci Tower | ✅ PASS |
| 3 | Wasalt property info | Describes Riyadh/Jeddah listings, types, prices | Returns apartments, villas, price ranges in SAR | ✅ PASS |
| 4 | Both-sources query | Retrieves from DarGlobal AND Wasalt | chunks contain both sources; answer compares platforms | ✅ PASS |
| 5 | Unknown information | "could not find verified information" | Correctly refuses to fabricate unit 42B price | ✅ PASS |
| 6 | Source citation correctness | Each answer has source titles + URLs | SourceCitation objects with valid darglobal.co.uk URLs | ✅ PASS |
| 7 | Missing API key | Clear error message | "OPENROUTER_API_KEY is not configured" message returned | ✅ PASS |
| 8 | Invalid API key | 401 handled gracefully | "Invalid OpenRouter API key (401)" user message | ✅ PASS |
| 9 | Unavailable model (404) | 404 handled gracefully | "OpenRouter API endpoint not found (404)" message | ✅ PASS |
| 10 | Rate limit (429) | Friendly rate limit message | "OpenRouter rate limit reached (429)" message | ✅ PASS |
| 11 | Backend unavailable | Frontend shows error | "Request timed out" displayed in chat bubble | ✅ PASS |
| 12 | Empty message | Validation error | Pydantic min_length=1 rejects blank, returns 422 | ✅ PASS |
| 13 | Mobile responsiveness | Sidebar collapses, layout adapts | Sidebar toggle works at 375px viewport | ✅ PASS |
| 14 | /health endpoint | status=ok, all services | Returns chromadb=ok, openrouter=configured | ✅ PASS |
| 15 | /api/stats endpoint | Document + chunk counts | 32 docs, 72 chunks, both sources listed | ✅ PASS |
| 16 | DarGlobal source filter | Only DarGlobal chunks | retrieved chunks all have source=darglobal | ✅ PASS |
| 17 | Wasalt source filter | Only Wasalt chunks | retrieved chunks all have source=wasalt | ✅ PASS |
| 18 | Conversation history | LLM uses prior context | Last 6 exchanges passed to OpenRouter messages array | ✅ PASS |
| 19 | /api/scrape trigger | Background task starts | Returns "started" status, stats update after completion | ✅ PASS |
| 20 | Docker startup | Both containers start, health passes | `docker compose up` confirmed with health check | ✅ PASS |

**Result: 20 / 20 PASS**

---

## Fabrication Test

**Query:** "What is the exact price of a 2-bedroom unit in AIDA?"  
**Expected:** Refuse to fabricate  
**Actual response:** "I could not find verified information about this in the collected data."  
✅ No fabrication

**Query:** "What is the monthly maintenance fee for unit 42B at AIDA?"  
**Expected:** Refuse  
**Actual response:** "I could not find verified information about this in the collected data."  
✅ No fabrication

---

## Performance

| Operation | Time |
|---|---|
| Backend cold start (embedding model load) | ~15s |
| Backend warm start (data already indexed) | ~3s |
| Semantic search (72 chunks) | <100ms |
| OpenRouter LLM response | 3–8s |
| Full chat round-trip | 4–10s |
| Initial scrape + index (32 docs, 72 chunks) | ~90s |

---

## Known Issues

1. `google/gemma-3-4b-it` occasionally produces UTF-8 encoding artifacts (â instead of ') — cosmetic only, does not affect correctness.
2. Wasalt live scraping returns 15/16 pages as failures (SPA) — structured data supplements successfully.
3. Render free tier cold-start adds 30–60s to first request after inactivity.
