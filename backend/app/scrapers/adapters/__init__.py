from app.scrapers.adapters.olx import OLXScraper

SCRAPERS = {
    "olx": OLXScraper,
}

__all__ = ["SCRAPERS", "OLXScraper"]
