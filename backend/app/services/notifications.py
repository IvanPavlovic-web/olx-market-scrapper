from typing import Any
import httpx
from app.core.config import settings
from app.core.logging import log


class TelegramNotifier:
    def __init__(self, token: str | None, default_chat: str | None = None):
        self.token = token
        self.default_chat = default_chat

    async def send(self, text: str, chat_id: str | None = None) -> bool:
        if not self.token:
            return False
        cid = chat_id or self.default_chat
        if not cid:
            return False
        url = f"https://api.telegram.org/bot{self.token}/sendMessage"
        try:
            async with httpx.AsyncClient() as c:
                r = await c.post(url, json={
                    "chat_id": cid,
                    "text": text,
                    "parse_mode": "HTML",
                    "disable_web_page_preview": False,
                }, timeout=10)
                return r.status_code == 200
        except Exception as e:
            log.warning("telegram_fail", err=str(e))
            return False


telegram = TelegramNotifier(settings.TELEGRAM_BOT_TOKEN, settings.TELEGRAM_CHAT_ID)


def format_listing_alert(listing: dict, rule_name: str) -> str:
    price = f"{listing['price']} {listing.get('currency', 'BAM')}" if listing.get("price") is not None else "—"
    return (
        f"🔔 <b>{rule_name}</b>\n\n"
        f"<b>{listing['title']}</b>\n"
        f"💰 {price}\n"
        f"📍 {listing.get('location', '—')}\n"
        f"🔗 {listing['url']}"
    )
