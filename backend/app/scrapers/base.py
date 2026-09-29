import abc
import asyncio
import hashlib
from dataclasses import dataclass, field
from typing import Any
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential_jitter
from app.core.config import settings
from app.core.logging import log
from app.services.proxy_pool import ProxyPool


@dataclass
class ScrapedListing:
    source: str
    external_id: str
    url: str
    title: str
    price: float | None = None
    currency: str = "BAM"
    location: str | None = None
    description: str | None = None
    seller_name: str | None = None
    images: list[str] = field(default_factory=list)
    attributes: dict[str, Any] = field(default_factory=dict)
    posted_at: str | None = None

    def hash_key(self) -> str:
        raw = f"{self.source}|{self.external_id}|{self.price}|{self.title}"
        return hashlib.sha256(raw.encode()).hexdigest()


class BaseScraper(abc.ABC):
    source: str = "base"

    def __init__(self, proxy_pool: ProxyPool | None = None):
        self.sem = asyncio.Semaphore(settings.SCRAPER_CONCURRENCY)
        self.proxy_pool = proxy_pool or ProxyPool(settings.PROXIES)
        self.headers = {
            "User-Agent": settings.SCRAPER_USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/json;q=0.9",
            "Accept-Language": "bs,hr,sr,en;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
        }

    @retry(stop=stop_after_attempt(3), wait=wait_exponential_jitter(0.5, 3.0), reraise=True)
    async def fetch(self, client: httpx.AsyncClient, url: str, *, use_proxy: bool = True) -> httpx.Response:
        proxy = self.proxy_pool.get() if use_proxy else None
        request_client = httpx.AsyncClient(http2=True, proxy=proxy) if proxy else client
        try:
            resp = await request_client.get(
                url,
                timeout=settings.SCRAPER_TIMEOUT,
                headers=self.headers,
                follow_redirects=True,
            )
            resp.raise_for_status()
            if proxy:
                self.proxy_pool.mark_good(proxy)
            return resp
        except Exception as e:
            if proxy:
                self.proxy_pool.mark_bad(proxy)
            log.warning("fetch_failed", url=url, proxy=proxy, err=str(e))
            raise
        finally:
            if request_client is not client:
                await request_client.aclose()

    def make_client(self):
        return httpx.AsyncClient(http2=True)

    @abc.abstractmethod
    async def list_category(self, category_url: str, page: int = 1) -> list[ScrapedListing]: ...
