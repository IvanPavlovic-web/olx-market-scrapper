from datetime import datetime, timezone
from urllib.parse import parse_qs, urlencode, urlsplit

from app.scrapers.base import BaseScraper, ScrapedListing
from app.core.logging import log

BASE = "https://olx.ba"
API_BASE = "https://api.olx.ba"
CATEGORY_IDS = {
    "automobili": 18,
    "dijelovi-opreme": 928,
    "dijelovi-za-vozila": 928,
    "mobilni-telefoni": 3,
    "mobilni-uredjaji": 3,
    "racunari": 5,
    "kompjuteri": 5,
    "namjestaj": 701,
    "moj-dom": 701,
}


class OLXScraper(BaseScraper):
    source = "olx"

    async def list_category(self, category_url: str, page: int = 1) -> list[ScrapedListing]:
        query = parse_qs(urlsplit(category_url.replace("{page}", str(page))).query)
        category_slug = query.get("category", [""])[0]
        category_id = query.get("category_id", [None])[0] or CATEGORY_IDS.get(category_slug)
        if category_id is None:
            log.warning("olx_unknown_category", category=category_slug)
            return []

        params = {"category_id": category_id, "page": page}
        if query.get("q", [None])[0]:
            params["q"] = query["q"][0]
        url = f"{API_BASE}/search?{urlencode(params)}"
        async with self.make_client() as client:
            try:
                response = await self.fetch(client, url)
                records = response.json().get("data", [])
            except Exception as exc:
                log.warning("olx_search_failed", category=category_slug, page=page, err=str(exc))
                return []
        listings = [self._to_listing(record) for record in records if isinstance(record, dict)]
        listings = [listing for listing in listings if listing is not None]
        log.info("olx_list", category=category_slug, page=page, found=len(listings))
        return listings

    def _to_listing(self, record: dict) -> ScrapedListing | None:
        listing_id = record.get("id")
        title = record.get("title")
        if not listing_id or not title:
            return None

        try:
            price = float(record["price"]) if record.get("price") is not None else None
        except (TypeError, ValueError):
            price = None

        location = record.get("location")
        if isinstance(location, dict):
            location = location.get("name") or location.get("label")
        elif isinstance(location, list):
            location = ", ".join(str(part) for part in location if part)
        elif not isinstance(location, str):
            location = None

        images = record.get("images") or []
        if not images and record.get("image"):
            images = [record["image"]]
        images = [image for image in images if isinstance(image, str)][:20]

        posted_at = record.get("date")
        if isinstance(posted_at, (int, float)):
            posted_at = datetime.fromtimestamp(posted_at, timezone.utc).isoformat()

        return ScrapedListing(
            source=self.source,
            external_id=str(listing_id),
            url=f"{BASE}/artikal/{listing_id}",
            title=str(title),
            price=price,
            currency="BAM",
            location=location,
            images=images,
            attributes={
                "category_id": record.get("category_id"),
                "city_id": record.get("city_id"),
            },
            posted_at=str(posted_at) if posted_at else None,
        )
