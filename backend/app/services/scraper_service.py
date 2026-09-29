import asyncio
from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from app.core.database import SessionLocal
from app.core.logging import log
from app.core.config import settings
from app.models import Listing, PriceHistory, Category
from app.scrapers.adapters import SCRAPERS
from app.services.proxy_pool import ProxyPool


class ScraperService:
    def __init__(self):
        self.proxy_pool = ProxyPool(settings.PROXIES)
        self.instances = {name: cls(proxy_pool=self.proxy_pool) for name, cls in SCRAPERS.items()}

    def register(self, name: str, cls):
        self.instances[name] = cls(proxy_pool=self.proxy_pool)

    async def scrape_category(self, source: str, category_slug: str, max_pages: int = 3):
        scraper = self.instances.get(source)
        if not scraper:
            log.warning("no_scraper", source=source)
            return

        url_tpl = f"https://olx.ba/pretraga?page={{page}}&category={category_slug}"

        pages = await asyncio.gather(
            *(scraper.list_category(url_tpl, page=i) for i in range(1, max_pages + 1)),
            return_exceptions=True,
        )
        listings_by_id = {}
        for p in pages:
            if isinstance(p, list):
                listings_by_id.update({item.external_id: item for item in p})
            elif isinstance(p, Exception):
                log.warning("category_page_fail", category=category_slug, err=str(p))
        listings = list(listings_by_id.values())
        log.info("collected_listings", source=source, category=category_slug, n=len(listings))

        if not listings:
            return

        changed_listing_ids: list[str] = []
        async with SessionLocal() as db:
            category = await db.scalar(
                select(Category).where(Category.source == source, Category.slug == category_slug)
            )
            if category is None:
                category = Category(
                    source=source,
                    slug=category_slug,
                    name=category_slug.replace("-", " ").title(),
                    url=f"https://olx.ba/pretraga?category={category_slug}",
                )
                db.add(category)
                await db.flush()

            for item in listings:
                lid = await self._upsert(db, item, category.id)
                if lid:
                    changed_listing_ids.append(lid)
            await db.commit()

        # Dispatch alert evaluaciju
        from app.workers.tasks import evaluate_alerts_for_listing
        for lid in changed_listing_ids:
            try:
                evaluate_alerts_for_listing.delay(lid)
            except Exception as e:
                log.warning("celery_dispatch_fail", err=str(e))

    async def _upsert(self, db, item, category_id: int) -> str | None:
        price_dec = Decimal(str(item.price)) if item.price is not None else None
        now = datetime.now(timezone.utc)
        existing = (await db.execute(
            select(Listing.id, Listing.price, Listing.title, Listing.location).where(
                Listing.source == item.source,
                Listing.external_id == item.external_id,
            )
        )).one_or_none()
        changed = existing is None or any((
            existing.price != price_dec,
            existing.title != item.title,
            existing.location != item.location,
        ))

        stmt = pg_insert(Listing).values(
            source=item.source,
            external_id=item.external_id,
            url=item.url,
            title=item.title,
            description=item.description,
            price=price_dec,
            currency=item.currency,
            location=item.location,
            seller_name=item.seller_name,
            images=item.images,
            attributes=item.attributes,
            category_id=category_id,
            last_seen_at=now,
            is_active=True,
            raw_hash=item.hash_key(),
        ).on_conflict_do_update(
            index_elements=["source", "external_id"],
            set_={
                "price": price_dec,
                "title": item.title,
                "location": item.location,
                "last_seen_at": now,
                "is_active": True,
                "raw_hash": item.hash_key(),
                "attributes": item.attributes,
            },
        ).returning(Listing.id)

        row = (await db.execute(stmt)).first()
        if not row:
            return None

        listing_id = row[0]

        if existing is None or existing.price != price_dec:
            db.add(PriceHistory(
                listing_id=listing_id,
                price=price_dec,
                currency=item.currency,
                is_active=True,
                captured_at=now,
            ))
        return str(listing_id) if changed else None


scraper_service = ScraperService()
