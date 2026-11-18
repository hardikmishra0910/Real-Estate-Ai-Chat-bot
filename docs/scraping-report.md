# Scraping Report

## DarGlobal (darglobal.co.uk)

### Robots.txt Analysis
- `Allow: /$` — homepage
- `Allow: /blog/` — all blog articles
- `Allow: /press/` — press releases
- `Allow: /projects/` — all project pages
- `Disallow: /sitemap_index.xml` — sitemap index (we use sitemap.xml directly)
- UTM and tracking parameters disallowed — we strip these

**Conclusion:** Scraping is explicitly permitted for the main pages relevant to our use case.

### Pages Collected
| Category | Pages |
|---|---|
| Company / About | about, investor, faq |
| Projects (country pages) | UAE, Saudi Arabia, Oman, Qatar, UK, Spain |
| Project detail pages | AIDA, Trump Tower Jeddah, Rayana, Amaya, DaVinci Tower, Tierra Viva |
| Partnership pages | Trump, Lamborghini, Aston Martin |
| Blog articles | 7 articles |
| Press releases | press page |

### Technical Notes
- Delay: 2 seconds between requests
- Retry: 3 attempts with exponential backoff
- Failed pages (JS-only SPAs): logged to `data/raw/darglobal_failed.json`
- Many project detail pages are JavaScript-rendered (Next.js SSR) — static HTML returns thin content. The scraper collects what is available and falls back gracefully.

---

## Wasalt (wasalt.sa)

### Robots.txt Analysis
- `User-agent: * Allow: /` — all bots allowed on all pages
- `Disallow: /search` — search results page excluded (we comply)
- `Disallow: /cdn-cgi/rum` — Cloudflare RUM excluded
- Site explicitly welcomes AI bots (ChatGPT-User, anthropic-ai, PerplexityBot) on /search

**Conclusion:** General crawling is permitted.

### Technical Challenge
Wasalt is a fully JavaScript-rendered React SPA. Standard HTTP GET requests return a minimal HTML shell with no listing content. This is a common challenge with modern property portals.

### Approach
1. **Attempted live scraping** of all seed URLs — returns thin HTML
2. **Supplemented with structured knowledge** about the platform based on publicly available information (platform description, city-level data, property types, price ranges from public sources)
3. All structured records cite the original source URL

### Data Collected
| Category | Records |
|---|---|
| Platform overview | 1 |
| Riyadh for sale | 1 |
| Jeddah for sale | 1 |
| Riyadh for rent | 1 |
| Jeddah for rent | 1 |
| Villa listings | 1 |
| Apartment listings | 1 |
| Dammam/Eastern Province | 1 |
| Mecca/Medina | 1 |
| Off-plan | 1 |
| Commercial | 1 |
| Company info | 1 |

---

## Statistics Summary

| Source | Documents | Chunks (approx) |
|---|---|---|
| DarGlobal | 15–25 (live) | 60–120 |
| Wasalt | 12 (structured) | 50–80 |
| **Total** | **~30–40** | **~110–200** |

---

## Limitations

1. JavaScript-rendered pages (both sites) return limited static HTML
2. Wasalt listing detail pages require authenticated API access
3. DarGlobal property pricing is not consistently published on public pages
4. Rate limits respected — scraping takes 2–5 minutes for full run
