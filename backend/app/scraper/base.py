"""Base scraper with shared utilities, retry logic and rate limiting."""

import time
import json
import hashlib
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import requests
from bs4 import BeautifulSoup
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from app.core.logging import get_logger

logger = get_logger(__name__)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (compatible; EstateIQBot/1.0; "
        "+https://github.com/estateiq/estateiq; research/educational)"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
}


class ScrapingError(Exception):
    pass


class BaseScraper(ABC):
    """Abstract base class for all scrapers."""

    source_name: str = ""
    base_url: str = ""

    def __init__(self, delay: float = 2.0, max_pages: int = 50):
        self.delay = delay
        self.max_pages = max_pages
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
        self.scraped_urls: set[str] = set()
        self.failed_urls: list[dict] = []
        self.stats = {"pages_attempted": 0, "pages_succeeded": 0, "pages_failed": 0}

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((requests.ConnectionError, requests.Timeout)),
        reraise=False,
    )
    def _get(self, url: str, timeout: int = 15) -> Optional[requests.Response]:
        """Fetch a URL with retry logic."""
        self.stats["pages_attempted"] += 1
        try:
            resp = self.session.get(url, timeout=timeout, allow_redirects=True)
            if resp.status_code == 404:
                self.stats["pages_failed"] += 1
                self.failed_urls.append({"url": url, "reason": "404"})
                return None
            if resp.status_code in (403, 429, 503):
                logger.warning(f"Blocked/rate-limited on {url}: {resp.status_code}")
                self.stats["pages_failed"] += 1
                self.failed_urls.append({"url": url, "reason": str(resp.status_code)})
                return None
            resp.raise_for_status()
            self.stats["pages_succeeded"] += 1
            return resp
        except requests.RequestException as e:
            self.stats["pages_failed"] += 1
            self.failed_urls.append({"url": url, "reason": str(e)[:80]})
            return None

    def fetch_soup(self, url: str) -> Optional[BeautifulSoup]:
        """Fetch URL and return parsed BeautifulSoup, respecting delay."""
        if url in self.scraped_urls:
            return None
        self.scraped_urls.add(url)
        time.sleep(self.delay)
        resp = self._get(url)
        if resp is None:
            return None
        return BeautifulSoup(resp.text, "lxml")

    @staticmethod
    def clean_text(text: str) -> str:
        """Remove excess whitespace and newlines."""
        if not text:
            return ""
        lines = [line.strip() for line in text.splitlines()]
        return " ".join(line for line in lines if line)

    @staticmethod
    def doc_id(url: str) -> str:
        return hashlib.md5(url.encode()).hexdigest()

    @staticmethod
    def now_iso() -> str:
        return datetime.now(timezone.utc).isoformat()

    @abstractmethod
    def scrape(self) -> list[dict]:
        """Run the scraper and return a list of document dicts."""
        pass

    def save(self, documents: list[dict], output_path: Path) -> None:
        """Save documents to a JSONL file."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            for doc in documents:
                f.write(json.dumps(doc, ensure_ascii=False) + "\n")
        logger.info(f"Saved {len(documents)} documents to {output_path}")

    def print_stats(self) -> None:
        logger.info(
            f"[{self.source_name}] Scraping stats: "
            f"attempted={self.stats['pages_attempted']}, "
            f"succeeded={self.stats['pages_succeeded']}, "
            f"failed={self.stats['pages_failed']}, "
            f"failed_urls={len(self.failed_urls)}"
        )
