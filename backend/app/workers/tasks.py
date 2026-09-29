import asyncio
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from uuid import UUID
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload
from celery.signals import worker_process_init, worker_process_shutdown
from app.core.config import settings
from app.core.logging import log
from app.core.database import SessionLocal, engine
from app.models import Listing, PriceHistory, AlertRule, AlertMatch, User
from app.services.scraper_service import scraper_service
from app.services.notifications import telegram, format_listing_alert
from app.websocket.manager import ws_manager
from app.workers.celery_app import celery_app


POPULAR_CATEGORIES = [
    ("olx", "automobili"),
    ("olx", "dijelovi-opreme"),
    ("olx", "mobilni-telefoni"),
    ("olx", "racunari"),
    ("olx", "namjestaj"),
]
_worker_loop: asyncio.AbstractEventLoop | None = None


@worker_process_init.connect
def _start_worker_loop(**kwargs):
    global _worker_loop
    _worker_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(_worker_loop)


@worker_process_shutdown.connect
def _stop_worker_loop(**kwargs):
    if _worker_loop is not None and not _worker_loop.is_closed():
        try:
            _worker_loop.run_until_complete(engine.dispose())
        finally:
            _worker_loop.close()


def _run_async(coroutine):
    global _worker_loop
    if _worker_loop is None or _worker_loop.is_closed():
        _worker_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(_worker_loop)
    return _worker_loop.run_until_complete(coroutine)


@celery_app.task(name="app.workers.tasks.scrape_category_task", bind=True, max_retries=3)
def scrape_category_task(self, source: str, category_slug: str, max_pages: int = 3):
    try:
        _run_async(scraper_service.scrape_category(source, category_slug, max_pages))
    except Exception as exc:
        log.error("scrape_cat_fail", source=source, cat=category_slug, err=str(exc))
        raise self.retry(exc=exc, countdown=15)


@celery_app.task(name="app.workers.tasks.scrape_all_categories")
def scrape_all_categories():
    interval = max(settings.SCRAPE_INTERVAL_SECONDS, 60)
    stagger_seconds = max(interval // len(POPULAR_CATEGORIES), 1)
    for index, (source, slug) in enumerate(POPULAR_CATEGORIES):
        scrape_category_task.apply_async(
            args=(source, slug, 1),
            countdown=index * stagger_seconds,
        )


@celery_app.task(name="app.workers.tasks.evaluate_alerts_for_listing")
def evaluate_alerts_for_listing(listing_id: str):
    _run_async(_evaluate(listing_id))


async def _evaluate(listing_id: str):
    try:
        listing_uuid = UUID(listing_id)
    except ValueError:
        log.warning("invalid_listing_id", listing_id=listing_id)
        return

    async with SessionLocal() as db:
        listing = (await db.execute(
            select(Listing)
            .options(selectinload(Listing.category))
            .where(Listing.id == listing_uuid)
        )).scalar_one_or_none()
        if not listing:
            return

        rules = (await db.execute(select(AlertRule).where(AlertRule.is_active.is_(True)))).scalars().all()
        price_history = (await db.execute(
            select(PriceHistory.price)
            .where(PriceHistory.listing_id == listing_uuid, PriceHistory.price.is_not(None))
            .order_by(PriceHistory.captured_at.desc())
            .limit(2)
        )).scalars().all()
        previous_price = price_history[1] if len(price_history) > 1 else None
        notifications = []

        for rule in rules:
            if not _matches(rule, listing, previous_price):
                continue

            cooldown_cutoff = datetime.now(timezone.utc) - timedelta(seconds=rule.cooldown_seconds or 300)
            existing = (await db.execute(
                select(AlertMatch).where(
                    and_(AlertMatch.rule_id == rule.id,
                         AlertMatch.listing_id == listing.id,
                         AlertMatch.matched_at >= cooldown_cutoff)
                )
            )).scalar_one_or_none()
            if existing:
                continue

            payload = {
                "title": listing.title,
                "price": str(listing.price) if listing.price is not None else None,
                "currency": listing.currency,
                "url": listing.url,
                "location": listing.location,
            }
            db.add(AlertMatch(rule_id=rule.id, listing_id=listing.id, payload=payload))
            user = await db.get(User, rule.user_id)
            notifications.append((rule, user, payload))

        await db.commit()

        for rule, user, payload in notifications:
            if rule.notify_telegram and user is not None:
                await telegram.send(format_listing_alert(payload, rule.name), user.telegram_chat_id)
            if rule.notify_ws:
                await ws_manager.send_user(
                    rule.user_id,
                    {"type": "alert", "listing": payload, "rule_name": rule.name},
                )


def _matches(rule: AlertRule, listing: Listing, previous_price: Decimal | None) -> bool:
    if rule.source and rule.source.casefold() != listing.source.casefold():
        return False
    if rule.category_slug and listing.category and rule.category_slug.casefold() != listing.category.slug.casefold():
        return False
    if rule.location and rule.location.casefold() not in (listing.location or "").casefold():
        return False

    title = listing.title.casefold()
    keywords = [word.strip().casefold() for word in (rule.keywords or "").split(",") if word.strip()]
    excluded = [word.strip().casefold() for word in (rule.exclude_keywords or "").split(",") if word.strip()]
    if keywords and not all(word in title for word in keywords):
        return False
    if any(word in title for word in excluded):
        return False
    if rule.min_price is not None and (listing.price is None or listing.price < rule.min_price):
        return False
    if rule.max_price is not None and (listing.price is None or listing.price > rule.max_price):
        return False
    if rule.price_drop_percent:
        if not previous_price or listing.price is None:
            return False
        drop = (previous_price - listing.price) * 100 / previous_price
        if drop < rule.price_drop_percent:
            return False
    return True


@celery_app.task(name="app.workers.tasks.cleanup_stale_listings")
def cleanup_stale_listings():
    _run_async(_cleanup_stale_listings())


async def _cleanup_stale_listings() -> None:
    cutoff = datetime.now(timezone.utc) - timedelta(days=30)
    async with SessionLocal() as db:
        stale = (await db.execute(
            select(Listing).where(Listing.is_active.is_(True), Listing.last_seen_at < cutoff)
        )).scalars().all()
        for listing in stale:
            listing.is_active = False
        await db.commit()
