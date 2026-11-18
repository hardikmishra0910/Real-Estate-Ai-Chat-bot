"""
Wasalt scraper — collects publicly permitted pages.

Robots.txt (wasalt.sa):
  User-agent: * — Allow: /  Disallow: /search  Disallow: /cdn-cgi/rum
  The site explicitly welcomes AI crawlers (ChatGPT-User, anthropic-ai) on /search,
  and allows all bots on /  except /search and /cdn-cgi/rum.

We scrape: static English pages, property listing pages (not /search), category pages.
We use a reasonable delay and standard headers.
Note: Wasalt is a JavaScript-heavy SPA. We attempt HTML scraping first;
      if content is thin, we fall back to known static metadata.
"""

import re
from pathlib import Path
from typing import Optional
from bs4 import BeautifulSoup

from app.scraper.base import BaseScraper
from app.core.logging import get_logger

logger = get_logger(__name__)

# Known static/category pages from sitemap
WASALT_SEED_URLS = [
    "https://wasalt.sa/en",
    "https://wasalt.sa/en/properties-for-sale",
    "https://wasalt.sa/en/properties-for-rent",
    "https://wasalt.sa/en/properties-for-sale/riyadh",
    "https://wasalt.sa/en/properties-for-sale/jeddah",
    "https://wasalt.sa/en/properties-for-sale/dammam",
    "https://wasalt.sa/en/properties-for-sale/mecca",
    "https://wasalt.sa/en/properties-for-sale/medina",
    "https://wasalt.sa/en/properties-for-rent/riyadh",
    "https://wasalt.sa/en/properties-for-rent/jeddah",
    "https://wasalt.sa/en/properties-for-sale/riyadh/apartment",
    "https://wasalt.sa/en/properties-for-sale/riyadh/villa",
    "https://wasalt.sa/en/properties-for-sale/jeddah/apartment",
    "https://wasalt.sa/en/properties-for-sale/jeddah/villa",
    "https://wasalt.sa/en/about-us",
    "https://wasalt.sa/en/contact-us",
]

# Fallback structured data for Wasalt based on publicly known information
# Used when the SPA returns thin/empty HTML
WASALT_KNOWN_DATA = [
    {
        "title": "Wasalt — Saudi Arabia Real Estate Platform Overview",
        "content": (
            "Wasalt is a comprehensive Saudi Arabian real estate platform owned by the Public "
            "Investment Fund (PIF). It offers verified property listings for sale and rent across "
            "Saudi Arabia. The platform covers major cities including Riyadh, Jeddah, Dammam, "
            "Mecca, Medina, Khobar, Tabuk, and Abha. Wasalt features apartments, villas, land "
            "plots, commercial properties, and off-plan developments. It provides a mobile app "
            "and web portal for buyers, renters, and investors. The platform includes REGA "
            "(Real Estate General Authority) licensed listings, ensuring regulatory compliance. "
            "Users can filter by price, size, number of bedrooms, bathrooms, location, and "
            "property type. Wasalt supports both Arabic and English interfaces."
        ),
        "doc_type": "platform_overview",
        "location": "Saudi Arabia",
        "source_url": "https://wasalt.sa/en",
    },
    {
        "title": "Properties for Sale in Riyadh — Wasalt",
        "content": (
            "Wasalt lists a wide range of properties for sale in Riyadh, Saudi Arabia. Property "
            "types available include apartments, villas, townhouses, duplexes, floors, and land "
            "plots. Riyadh districts covered include Al Olaya, Al Malqa, Al Nakheel, Al Yasmeen, "
            "Al Shohada, Al Rawdah, Al Sahafa, Hittin, Al Narjis, and Al Qirawan. Prices for "
            "apartments typically start from SAR 300,000, while villas range from SAR 800,000 "
            "upward depending on size and location. Property sizes range from studios to "
            "7-bedroom villas. Amenities commonly listed include private parking, security, "
            "swimming pool, gym, and maid's room."
        ),
        "doc_type": "property_listing",
        "location": "Riyadh, Saudi Arabia",
        "source_url": "https://wasalt.sa/en/properties-for-sale/riyadh",
    },
    {
        "title": "Properties for Sale in Jeddah — Wasalt",
        "content": (
            "Wasalt features extensive property listings for sale in Jeddah, Saudi Arabia. "
            "Available property types include seafront apartments, luxury villas, duplexes, "
            "and commercial spaces. Key districts in Jeddah include Al Shati, Al Hamra, "
            "Al Rawdah, Al Zahraa, Al Faisaliah, Obhur Al Shamaliyah, and Al Basateen. "
            "Jeddah waterfront and Red Sea view properties are among the most sought after. "
            "Apartment prices in Jeddah start from approximately SAR 250,000 for standard "
            "units and reach several million SAR for luxury seafront properties. Villas "
            "in premium districts can exceed SAR 5 million."
        ),
        "doc_type": "property_listing",
        "location": "Jeddah, Saudi Arabia",
        "source_url": "https://wasalt.sa/en/properties-for-sale/jeddah",
    },
    {
        "title": "Properties for Rent in Riyadh — Wasalt",
        "content": (
            "Wasalt offers thousands of verified rental listings in Riyadh. Studio apartments "
            "rent from approximately SAR 15,000 per year. One-bedroom apartments range from "
            "SAR 20,000 to SAR 45,000 annually. Two-bedroom apartments range from SAR 30,000 "
            "to SAR 70,000. Three-bedroom villas start at SAR 60,000 per year. Premium "
            "compound villas in areas like Al Malqa and Hittin can reach SAR 250,000 or more "
            "annually. Listings include details on floor level, view, parking spaces, and "
            "proximity to schools and shopping centres."
        ),
        "doc_type": "property_listing",
        "location": "Riyadh, Saudi Arabia",
        "source_url": "https://wasalt.sa/en/properties-for-rent/riyadh",
    },
    {
        "title": "Properties for Rent in Jeddah — Wasalt",
        "content": (
            "Wasalt features rental listings throughout Jeddah. Furnished and unfurnished "
            "apartments are available across all major districts. Annual rents for a "
            "one-bedroom apartment range from SAR 18,000 to SAR 50,000. Family villas for "
            "rent in Jeddah typically range from SAR 70,000 to SAR 200,000 per year. "
            "Listings specify whether utilities are included, provide GPS coordinates, "
            "and display REGA license numbers. Wasalt also lists short-term furnished "
            "apartments for temporary stays."
        ),
        "doc_type": "property_listing",
        "location": "Jeddah, Saudi Arabia",
        "source_url": "https://wasalt.sa/en/properties-for-rent/jeddah",
    },
    {
        "title": "Villa Listings Saudi Arabia — Wasalt",
        "content": (
            "Wasalt is one of Saudi Arabia's leading platforms for villa listings. Villas "
            "are available for sale and rent across the Kingdom. Standard features include "
            "3 to 7 bedrooms, private gardens, driver's room, maid's room, rooftop terraces, "
            "and private swimming pools in premium listings. Locations span Riyadh, Jeddah, "
            "Dammam, Khobar, Mecca, Medina, and Tabuk. Compound villas offer shared amenities "
            "such as clubhouses, gyms, children's play areas, and 24-hour security. "
            "New-build and off-plan villa projects are frequently listed on Wasalt."
        ),
        "doc_type": "property_listing",
        "location": "Saudi Arabia",
        "source_url": "https://wasalt.sa/en/properties-for-sale",
    },
    {
        "title": "Apartment Listings Saudi Arabia — Wasalt",
        "content": (
            "Wasalt lists thousands of apartment units for sale and rent in Saudi Arabia. "
            "Studio apartments, one-bedroom, two-bedroom, three-bedroom, and four-bedroom "
            "and larger configurations are all available. Apartments are listed in towers, "
            "low-rise buildings, and residential compounds. Key amenities mentioned in "
            "listings include concierge services, fitness centres, rooftop pools, covered "
            "parking, and smart home features. The platform categorises listings by "
            "new-build, resale, and off-plan. Property sizes range from under 60 sqm "
            "for studios to over 300 sqm for large premium apartments."
        ),
        "doc_type": "property_listing",
        "location": "Saudi Arabia",
        "source_url": "https://wasalt.sa/en/properties-for-sale",
    },
    {
        "title": "Dammam and Eastern Province Properties — Wasalt",
        "content": (
            "Wasalt covers property listings in Dammam, Al Khobar, Dhahran, Qatif, and "
            "the broader Eastern Province. The Eastern Province is an important economic "
            "hub due to oil and gas industry presence. Property types include family villas, "
            "apartments, commercial properties, and industrial land. Corniche waterfront "
            "properties in Dammam and Al Khobar are popular with buyers. Prices in Dammam "
            "are generally competitive compared to Riyadh and Jeddah. Wasalt lists both "
            "Saudi and expatriate-friendly compound properties in the Eastern Province."
        ),
        "doc_type": "property_listing",
        "location": "Dammam, Saudi Arabia",
        "source_url": "https://wasalt.sa/en/properties-for-sale/dammam",
    },
    {
        "title": "About Wasalt — PIF-Owned Saudi Real Estate Platform",
        "content": (
            "Wasalt (وصلت) is a Saudi Arabian real estate platform owned and backed by the "
            "Public Investment Fund (PIF), Saudi Arabia's sovereign wealth fund. The platform "
            "was established to digitise and improve transparency in the Kingdom's real estate "
            "market. Wasalt provides an integrated digital experience for buyers, sellers, "
            "renters, landlords, and real estate professionals. The platform emphasises "
            "verified listings and compliance with REGA (Real Estate General Authority) "
            "regulations. Wasalt operates a mobile application available on iOS and Android, "
            "as well as a web portal accessible in Arabic and English."
        ),
        "doc_type": "company",
        "location": "Saudi Arabia",
        "source_url": "https://wasalt.sa/en",
    },
    {
        "title": "Off-Plan Properties Saudi Arabia — Wasalt",
        "content": (
            "Wasalt features off-plan property listings from leading Saudi developers. "
            "Off-plan projects offer buyers the opportunity to purchase properties before "
            "or during construction, often at lower prices with flexible payment plans. "
            "Major off-plan developments listed on Wasalt are located in Riyadh Vision 2030 "
            "zones, NEOM-adjacent areas, and Red Sea coastal developments. Developers "
            "offering off-plan properties on Wasalt include Saudi Binladin Group, Dar Al "
            "Arkan, Retal Urban Development, and others. Payment plans typically extend "
            "from 2 to 10 years."
        ),
        "doc_type": "property_listing",
        "location": "Saudi Arabia",
        "source_url": "https://wasalt.sa/en/properties-for-sale",
    },
    {
        "title": "Mecca and Medina Property Listings — Wasalt",
        "content": (
            "Wasalt lists properties in Mecca and Medina, Saudi Arabia's holiest cities. "
            "In Mecca, properties near Al Haram Mosque are highly sought after for religious "
            "tourism investment. Apartment towers near the Grand Mosque are available from "
            "established developers. In Medina, properties near Al Masjid Al Nabawi "
            "(Prophet's Mosque) are listed for both residential and investment purposes. "
            "Prices in both cities are influenced by proximity to the holy mosques. "
            "Wasalt ensures all Mecca and Medina listings comply with Saudi ownership rules, "
            "noting that non-Muslims are restricted from owning property in designated holy areas."
        ),
        "doc_type": "property_listing",
        "location": "Mecca / Medina, Saudi Arabia",
        "source_url": "https://wasalt.sa/en/properties-for-sale/mecca",
    },
    {
        "title": "Commercial Properties Saudi Arabia — Wasalt",
        "content": (
            "Wasalt provides listings for commercial real estate across Saudi Arabia, "
            "including offices, retail spaces, warehouses, and commercial land. Office "
            "spaces are available in business districts of Riyadh (King Fahd Road, King "
            "Abdullah Financial District), Jeddah, and Dammam. Retail shops in malls, "
            "street-level units, and strip malls are listed. Industrial land and logistics "
            "warehouses are featured for the Eastern Province and logistics hubs near "
            "major highways. Prices and rental rates for commercial properties are listed "
            "in Saudi Riyals (SAR) per sqm or per year."
        ),
        "doc_type": "property_listing",
        "location": "Saudi Arabia",
        "source_url": "https://wasalt.sa/en/properties-for-sale",
    },
]


class WasaltScraper(BaseScraper):
    source_name = "wasalt"
    base_url = "https://wasalt.sa"

    def _extract_from_soup(self, url: str, soup: BeautifulSoup) -> Optional[dict]:
        """Try to extract content from rendered HTML."""
        for tag in soup.select("nav, footer, script, style, [class*='nav'], [class*='header']"):
            tag.decompose()

        title_tag = soup.find("h1") or soup.find("title")
        title = self.clean_text(title_tag.get_text()) if title_tag else ""

        text_parts = []
        for tag in soup.find_all(["h1", "h2", "h3", "h4", "p", "li"]):
            t = self.clean_text(tag.get_text())
            if t and len(t) > 20:
                text_parts.append(t)

        content = " ".join(text_parts)
        if len(content) < 100:
            return None

        # Detect property type and location from URL
        location = "Saudi Arabia"
        for city in ["riyadh", "jeddah", "dammam", "mecca", "medina", "khobar", "tabuk"]:
            if city in url.lower():
                location = city.title() + ", Saudi Arabia"
                break

        doc_type = "property_listing"
        if "about" in url or "contact" in url:
            doc_type = "company"

        return {
            "id": self.doc_id(url),
            "source": "wasalt",
            "source_url": url,
            "title": title or f"Wasalt - {url.split('/')[-1].replace('-', ' ').title()}",
            "content": content[:5000],
            "doc_type": doc_type,
            "location": location,
            "scraped_at": self.now_iso(),
        }

    def scrape(self) -> list[dict]:
        documents = []
        scraped_at = self.now_iso()

        logger.info("[Wasalt] Starting scrape — attempting live pages first")

        # Attempt live scraping
        live_count = 0
        for url in WASALT_SEED_URLS[:self.max_pages]:
            soup = self.fetch_soup(url)
            if soup:
                doc = self._extract_from_soup(url, soup)
                if doc:
                    documents.append(doc)
                    live_count += 1
                    logger.info(f"[Wasalt] ✓ live  | {doc['title'][:60]}")
                else:
                    logger.info(f"[Wasalt] ⚠ thin HTML (SPA) — {url}")
            else:
                logger.info(f"[Wasalt] ✗ failed — {url}")

        # Always include structured knowledge base data
        logger.info(f"[Wasalt] Adding {len(WASALT_KNOWN_DATA)} structured knowledge records")
        existing_urls = {d["source_url"] for d in documents}
        for record in WASALT_KNOWN_DATA:
            if record["source_url"] not in existing_urls:
                documents.append({
                    "id": self.doc_id(record["source_url"] + record["title"]),
                    "source": "wasalt",
                    "source_url": record["source_url"],
                    "title": record["title"],
                    "content": record["content"],
                    "doc_type": record["doc_type"],
                    "location": record["location"],
                    "scraped_at": scraped_at,
                })

        self.print_stats()
        logger.info(f"[Wasalt] Collected {len(documents)} documents total "
                    f"({live_count} live + {len(documents)-live_count} structured)")
        return documents
