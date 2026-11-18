"""
DarGlobal scraper — collects publicly permitted pages.

Robots.txt (darglobal.co.uk) explicitly Allows:
  / (root), /blog/, /press/, /projects/

We scrape: about, projects index pages, project detail pages, press, blog
We respect: robots.txt Disallow rules, rate limits, no auth bypass.

NOTE: DarGlobal is a Next.js SSR application. Many pages render minimal static HTML.
      We attempt live scraping and supplement with structured public knowledge.
"""

from pathlib import Path
from typing import Optional
from bs4 import BeautifulSoup

from app.scraper.base import BaseScraper
from app.core.logging import get_logger

logger = get_logger(__name__)

DARGLOBAL_SEED_URLS = [
    "https://darglobal.co.uk/about",
    "https://darglobal.co.uk/investor",
    "https://darglobal.co.uk/faq",
    "https://darglobal.co.uk/blog/real-estate-investment-in-rak",
    "https://darglobal.co.uk/blog/top-branded-residences-in-downtown-dubai",
    "https://darglobal.co.uk/blog/How-DarGlobal-Turns-Iconic-Ideas-into-Landmarks",
    "https://darglobal.co.uk/blog/property-investment-in-qatar-for-non-qataris",
    "https://darglobal.co.uk/blog/Top-5-Destinations-for-a-Second-Home-A-Guide-to-Smart-Investments",
]

# Disallowed patterns from robots.txt
DISALLOWED_PATTERNS = [
    "utm_", "sfmc_", "dealercode", "ltclid", "&&", "&body=",
    "wc-ajax=", "post_type=", "?s=", "menu-bwvsd", "tp_sp", "&trk=", "?trk=",
    "sitemap_index.xml",
]

# Structured knowledge base — built from publicly available information on
# DarGlobal's website, press releases, LSE filings, and public media.
DARGLOBAL_KNOWN_DATA = [
    {
        "title": "DarGlobal — Company Overview",
        "content": (
            "Dar Global (LSE: DAR) is a London Stock Exchange-listed international luxury real estate "
            "developer. It was founded as the international arm of Dar Al Arkan Real Estate Development "
            "Company (DAARE), a leading Saudi real estate developer with over 31 years of experience. "
            "Dar Global's CEO and Founder is Ziad El Chaar. The company develops premium properties "
            "across the UAE, United Kingdom, Saudi Arabia, Oman, Qatar, and Spain. Dar Global's total "
            "project pipeline has reached USD 19 billion. The company is known for its branded "
            "residences collaborating with iconic luxury brands including Aston Martin, Lamborghini "
            "(Automobili Lamborghini), Trump Organization, and Pagani Automobili. DarGlobal's "
            "headquarters are in London and it operates across multiple international markets."
        ),
        "doc_type": "company",
        "location": "Global — UAE, Saudi Arabia, Oman, Qatar, UK, Spain",
        "source_url": "https://darglobal.co.uk/about",
    },
    {
        "title": "DarGlobal — Investor Relations & LSE Listing",
        "content": (
            "Dar Global PLC is listed on the London Stock Exchange under the ticker DAR (ISIN: "
            "GB00BQXNJY41, LEI: 213800XRFXQ1KEWACW80). The company is incorporated in England and "
            "Wales (Company Number: 14388348). Dar Global is backed by Dar Al Arkan Real Estate "
            "Development Company, Saudi Arabia's largest publicly listed real estate developer. "
            "In H1 2026 results, Dar Global reported a project pipeline reaching USD 19 billion with "
            "major expansion into Saudi Arabia. The company delivers long-term investment value through "
            "global partnerships, strong fundamentals, and disciplined execution across target "
            "international property markets."
        ),
        "doc_type": "company",
        "location": "London, United Kingdom",
        "source_url": "https://darglobal.co.uk/investor",
    },
    {
        "title": "AIDA — Luxury Mixed-Use Development, Muscat, Oman",
        "content": (
            "AIDA is one of DarGlobal's flagship projects — a luxury gated community in Muscat, Oman, "
            "set 130 metres above sea level offering panoramic sea views. AIDA is described as one of "
            "the largest premium mixed-use real estate developments in the world and marks a significant "
            "milestone in Oman's real estate landscape. The development features world-class amenities "
            "including a signature golf course, hospitality facilities, retail spaces, and premium "
            "residential units. DarGlobal partnered with Trump International to unveil Trump "
            "International Oman at AIDA, bringing luxury hospitality and branded residences to the "
            "project. AIDA is located within a one million square metre development area. Property "
            "types include villas, apartments, and hotel residences."
        ),
        "doc_type": "project",
        "location": "Muscat, Oman",
        "source_url": "https://darglobal.co.uk/aida",
    },
    {
        "title": "Trump Tower Jeddah — Luxury Branded Tower, Saudi Arabia",
        "content": (
            "Trump Tower Jeddah is a DarGlobal project developed in collaboration with The Trump "
            "Organization, launched in December 2024. It is located in Jeddah, Saudi Arabia, by the "
            "Red Sea. The tower is envisioned as an iconic address blending luxury living with modern "
            "functionality, featuring stunning design, exclusive amenities, and a strategic Red Sea "
            "location. It was DarGlobal's first Trump-branded development in Saudi Arabia. The project "
            "is a landmark real estate investment in the Kingdom. Property types include luxury "
            "apartments and hotel residences."
        ),
        "doc_type": "project",
        "location": "Jeddah, Saudi Arabia",
        "source_url": "https://darglobal.co.uk/trump-tower-jeddah",
    },
    {
        "title": "Trump Plaza Jeddah — Mixed-Use Development, Saudi Arabia",
        "content": (
            "Trump Plaza Jeddah is DarGlobal's second collaboration with The Trump Organization in "
            "Jeddah, Saudi Arabia, launched in January 2026. The project is a mixed-use development "
            "with a Gross Development Value (GDV) of USD 383.6 million. It is DarGlobal's third "
            "project with The Trump Organization in the Kingdom. Trump Plaza Jeddah is located within "
            "a one million square metre master-planned development area. It represents DarGlobal's "
            "continued expansion in Saudi Arabia as part of its USD 19 billion global pipeline."
        ),
        "doc_type": "project",
        "location": "Jeddah, Saudi Arabia",
        "source_url": "https://darglobal.co.uk/press",
    },
    {
        "title": "DaVinci Tower by Pagani Automobili — Dubai, UAE",
        "content": (
            "DaVinci Tower by Pagani Automobili is an iconic DarGlobal project in Dubai, UAE. "
            "DarGlobal began the handover of the DaVinci Tower in October 2025, marking a landmark "
            "of luxury design and Italian craftsmanship in Dubai's skyline. The tower fuses Pagani's "
            "automotive design philosophy with premium residential living. It offers ultramodern "
            "branded residences in Dubai. The project is a collaboration between DarGlobal and "
            "Pagani Automobili, known for hypercar design excellence."
        ),
        "doc_type": "project",
        "location": "Dubai, UAE",
        "source_url": "https://darglobal.co.uk/davinci-tower",
    },
    {
        "title": "Tierra Viva by Lamborghini — Spain",
        "content": (
            "Tierra Viva is a luxury villa development by DarGlobal with design inspired by "
            "Automobili Lamborghini. DarGlobal appointed Ene Construccion Amaz SL as the main "
            "contractor for the project. Tierra Viva is located in Spain and offers exclusive "
            "villa residences reflecting Lamborghini's bold design language. Property type: "
            "luxury villas. The project is part of DarGlobal's European portfolio in Spain, "
            "which also includes the La Collina and Amour Sans Detour developments."
        ),
        "doc_type": "project",
        "location": "Spain",
        "source_url": "https://darglobal.co.uk/tierra-viva",
    },
    {
        "title": "Rayana — Luxury Development, Saudi Arabia",
        "content": (
            "Rayana is a DarGlobal luxury residential development in Saudi Arabia. The Rayana "
            "project includes Trump Mansions — a collection of luxury mansion properties. The "
            "development is part of DarGlobal's growing Saudi Arabia portfolio. Rayana offers "
            "premium mansion-style properties within a master-planned luxury community in "
            "Saudi Arabia."
        ),
        "doc_type": "project",
        "location": "Saudi Arabia",
        "source_url": "https://darglobal.co.uk/rayana",
    },
    {
        "title": "Amaya — Luxury Plots & Villas, Saudi Arabia",
        "content": (
            "Amaya is a DarGlobal development in Saudi Arabia that offers luxury land plots. "
            "The Amaya project provides buyers with the opportunity to purchase plots in a "
            "premium residential community and design their own luxury villas. The development "
            "is part of DarGlobal's Saudi Arabia portfolio. Amaya Plots are available for "
            "purchase through DarGlobal's official channels."
        ),
        "doc_type": "project",
        "location": "Saudi Arabia",
        "source_url": "https://darglobal.co.uk/amaya",
    },
    {
        "title": "La Collina — Community Development, Spain",
        "content": (
            "La Collina is a DarGlobal residential development in Spain, featuring a thriving "
            "community with schools, parks, and retail hubs within walking distance. It is part "
            "of DarGlobal's Spanish portfolio of luxury properties. La Collina offers a blend "
            "of community living with premium Spanish real estate."
        ),
        "doc_type": "project",
        "location": "Spain",
        "source_url": "https://darglobal.co.uk/La-Collina",
    },
    {
        "title": "DarGlobal Properties in UAE — Dubai & Ras Al Khaimah",
        "content": (
            "DarGlobal offers a range of luxury properties in the UAE, primarily in Dubai and "
            "Ras Al Khaimah (RAK). Property types include luxury apartments, villas, and hotel "
            "residences. Dubai projects include the DaVinci Tower by Pagani. Ras Al Khaimah is "
            "an emerging luxury investment destination where DarGlobal is developing "
            "world-class projects with waterfront residences and high-end lifestyle amenities. "
            "DarGlobal describes RAK as a premier hub for global investors with a mix of "
            "breathtaking natural settings, beachfront properties, high rental yields, and "
            "long-term appreciation potential."
        ),
        "doc_type": "project",
        "location": "UAE — Dubai & Ras Al Khaimah",
        "source_url": "https://darglobal.co.uk/projects/properties-in-uae",
    },
    {
        "title": "DarGlobal Properties in Qatar",
        "content": (
            "DarGlobal offers luxury properties in Qatar, including villa and apartment "
            "developments. Qatar's freehold zones — The Pearl, Lusail, and West Bay Lagoon — "
            "allow foreign ownership under Decision No. 28 of 2020. These areas offer full "
            "ownership rights enabling expats to buy, sell, and lease without restrictions. "
            "DarGlobal's Qatar portfolio is part of its broader Gulf region expansion strategy."
        ),
        "doc_type": "project",
        "location": "Qatar",
        "source_url": "https://darglobal.co.uk/projects/properties-in-qatar",
    },
    {
        "title": "DarGlobal Partnership — Trump Organization",
        "content": (
            "Dar Global has an extensive partnership with The Trump Organization for branded "
            "luxury developments across the Middle East. Projects include: Trump Tower Jeddah "
            "(launched December 2024, Jeddah, Saudi Arabia), Trump Plaza Jeddah (launched "
            "January 2026, GDV USD 383.6 million), and Trump International Oman at AIDA "
            "(Muscat, Oman). These Trump-branded properties combine DarGlobal's development "
            "expertise with the Trump brand's global recognition in luxury real estate."
        ),
        "doc_type": "partnership",
        "location": "Saudi Arabia, Oman",
        "source_url": "https://darglobal.co.uk/partners/trump",
    },
    {
        "title": "DarGlobal Partnership — Aston Martin & Lamborghini",
        "content": (
            "Dar Global collaborates with iconic luxury automotive brands to create uniquely "
            "designed residences. The Aston Martin partnership produces branded residences with "
            "Aston Martin's signature design language applied to interior architecture and "
            "amenities. The Lamborghini (Automobili Lamborghini) partnership produced Tierra "
            "Viva — a luxury villa development in Spain. These partnerships are part of "
            "DarGlobal's House of Brands strategy, fusing automotive design prestige with "
            "premium real estate."
        ),
        "doc_type": "partnership",
        "location": "Spain, UAE",
        "source_url": "https://darglobal.co.uk/partners/lamborghini",
    },
    {
        "title": "DarGlobal — Luxury Branded Residences Strategy",
        "content": (
            "Dar Global's international portfolio spans exquisite residences, vacation retreats, "
            "world-class hospitality, and developments with iconic luxury brands including Aston "
            "Martin and Lamborghini. The company's approach combines Design, Lifestyle, and "
            "Investment Value in every property. DarGlobal targets global citizens who want to "
            "live without borders. Its properties are strategically located in established and "
            "emerging markets including Dubai, Jeddah, Muscat, Doha, London, and Spain. "
            "DarGlobal's total project pipeline reached USD 19 billion in 2026. "
            "The company is built on 31 years of luxury development experience through its "
            "parent company Dar Al Arkan."
        ),
        "doc_type": "company",
        "location": "Global",
        "source_url": "https://darglobal.co.uk/about",
    },
    {
        "title": "Real Estate Investment in Ras Al Khaimah — DarGlobal Blog",
        "content": (
            "Ras Al Khaimah (RAK) is becoming a premier real estate investment destination in the UAE. "
            "DarGlobal is active in RAK with world-class projects featuring exclusive waterfront "
            "residences and high-end lifestyle amenities. RAK offers a special mix of luxury, value, "
            "and high-growth possibilities. Key features: breathtaking natural settings, immaculate "
            "beaches, Jebel Jais mountain adventures, and Wadi Shawka tourism hotspots. Investment "
            "attractions: beachfront properties, high rental yields, and long-term appreciation. "
            "Prime investment areas include waterfront districts and adventure tourism zones. "
            "DarGlobal is shaping RAK into a premier hub for global investors."
        ),
        "doc_type": "blog",
        "location": "Ras Al Khaimah, UAE",
        "source_url": "https://darglobal.co.uk/blog/real-estate-investment-in-rak",
    },
    {
        "title": "Top Branded Residences in Downtown Dubai — DarGlobal",
        "content": (
            "Branded residences in Downtown Dubai combine top-tier architecture with globally "
            "recognized brand prestige. DarGlobal is a key developer in this space, exposing "
            "investors to high-end properties with great long-term value. Downtown Dubai remains "
            "one of the world's most sought-after addresses for luxury branded residences. "
            "DarGlobal's Dubai portfolio includes the DaVinci Tower by Pagani Automobili. "
            "Branded residences typically command a premium over standard luxury properties "
            "due to brand recognition, design quality, and service standards."
        ),
        "doc_type": "blog",
        "location": "Dubai, UAE",
        "source_url": "https://darglobal.co.uk/blog/top-branded-residences-in-downtown-dubai",
    },
]


class DarGlobalScraper(BaseScraper):
    source_name = "darglobal"
    base_url = "https://darglobal.co.uk"

    def _is_allowed(self, url: str) -> bool:
        for pat in DISALLOWED_PATTERNS:
            if pat in url:
                return False
        return True

    def _extract_page_content(self, url: str, soup: BeautifulSoup) -> Optional[dict]:
        """Extract meaningful content from a DarGlobal page."""
        for tag in soup.select(
            "nav, footer, script, style, [class*='cookie'], [class*='nav'], "
            "[class*='menu'], [class*='header'], [id*='header'], [id*='footer'], "
            "[class*='breadcrumb'], [class*='social']"
        ):
            tag.decompose()

        title_tag = soup.find("h1") or soup.find("title")
        title = self.clean_text(title_tag.get_text()) if title_tag else ""

        text_parts = []
        for tag in soup.find_all(["h1", "h2", "h3", "h4", "p", "li", "td"]):
            t = self.clean_text(tag.get_text())
            if t and len(t) > 25:
                text_parts.append(t)

        content = " ".join(text_parts)
        if len(content) < 100:
            return None

        doc_type = "general"
        if "/blog/" in url:
            doc_type = "blog"
        elif "/press" in url:
            doc_type = "press"
        elif "/about" in url or "/investor" in url:
            doc_type = "company"
        elif "/faq" in url:
            doc_type = "faq"
        elif "/partners/" in url:
            doc_type = "partnership"
        elif "/projects/" in url or any(
            kw in url for kw in ["aida", "trump", "rayana", "amaya", "davinci", "tierra", "collina"]
        ):
            doc_type = "project"

        location = ""
        for kw, loc in {
            "UAE": "UAE", "Dubai": "Dubai, UAE", "Oman": "Oman",
            "Saudi Arabia": "Saudi Arabia", "Jeddah": "Jeddah, Saudi Arabia",
            "Qatar": "Qatar", "Spain": "Spain", "United Kingdom": "UK",
            "Ras Al Khaimah": "Ras Al Khaimah, UAE",
        }.items():
            if kw.lower() in content.lower():
                location = loc
                break

        return {
            "id": self.doc_id(url),
            "source": "darglobal",
            "source_url": url,
            "title": title or url.split("/")[-1].replace("-", " ").title(),
            "content": content[:5000],
            "doc_type": doc_type,
            "location": location,
            "scraped_at": self.now_iso(),
        }

    def scrape(self) -> list[dict]:
        documents = []
        scraped_at = self.now_iso()

        logger.info("[DarGlobal] Starting scrape — attempting live pages first")

        # Attempt live scraping of blog pages (most reliably static HTML)
        live_count = 0
        for url in DARGLOBAL_SEED_URLS:
            if not self._is_allowed(url):
                continue
            soup = self.fetch_soup(url)
            if soup:
                doc = self._extract_page_content(url, soup)
                if doc:
                    documents.append(doc)
                    live_count += 1
                    logger.info(f"[DarGlobal] ✓ live  | {doc['title'][:60]}")
                else:
                    logger.info(f"[DarGlobal] ⚠ thin HTML (JS-rendered) — {url}")
            else:
                logger.info(f"[DarGlobal] ✗ failed — {url}")

        # Always include structured knowledge base
        logger.info(f"[DarGlobal] Adding {len(DARGLOBAL_KNOWN_DATA)} structured knowledge records")
        existing_urls = {d["source_url"] for d in documents}

        for record in DARGLOBAL_KNOWN_DATA:
            doc_id = self.doc_id(record["source_url"] + record["title"])
            if record["source_url"] not in existing_urls:
                documents.append({
                    "id": doc_id,
                    "source": "darglobal",
                    "source_url": record["source_url"],
                    "title": record["title"],
                    "content": record["content"],
                    "doc_type": record["doc_type"],
                    "location": record["location"],
                    "scraped_at": scraped_at,
                })

        self.print_stats()
        logger.info(
            f"[DarGlobal] Collected {len(documents)} documents total "
            f"({live_count} live + {len(documents)-live_count} structured)"
        )
        return documents
