"""
Repeatable scraping command.

Usage:
  python scripts/scrape.py                     # scrape both sources
  python scripts/scrape.py --source darglobal  # only DarGlobal
  python scripts/scrape.py --source wasalt     # only Wasalt
  python scripts/scrape.py --force             # force re-scrape even if cache exists
  python scripts/scrape.py --no-index          # scrape only, skip ChromaDB indexing
"""

import sys
import argparse
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from app.core.logging import setup_logging
from app.services.ingestion_service import run_ingestion

setup_logging()


def main():
    parser = argparse.ArgumentParser(description="EstateIQ data scraper")
    parser.add_argument(
        "--source",
        choices=["darglobal", "wasalt", "both"],
        default="both",
        help="Which source to scrape (default: both)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force re-scrape even if cached data exists",
    )
    parser.add_argument(
        "--no-index",
        action="store_true",
        help="Scrape only — skip ChromaDB indexing",
    )
    args = parser.parse_args()

    sources = ["darglobal", "wasalt"] if args.source == "both" else [args.source]

    print(f"\n{'='*50}")
    print(f"  EstateIQ Scraper")
    print(f"  Sources  : {', '.join(sources)}")
    print(f"  Force    : {args.force}")
    print(f"  Index    : {not args.no_index}")
    print(f"{'='*50}\n")

    result = run_ingestion(sources=sources, force_refresh=args.force)

    print(f"\n{'='*50}")
    print(f"  Scraping Complete")
    print(f"  Documents : {result['total_documents']}")
    print(f"  Chunks    : {result['total_chunks']}")
    print(f"  Indexed   : {result['indexed_chunks']}")
    print(f"  Timestamp : {result['timestamp']}")
    print(f"{'='*50}\n")

    for src, stat in result.get("sources", {}).items():
        print(f"  [{src}] docs={stat.get('documents', 0)}  source={stat.get('source', '?')}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
