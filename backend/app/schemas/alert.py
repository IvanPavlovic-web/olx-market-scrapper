from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field


class AlertRuleBase(BaseModel):
    name: str
    source: Optional[str] = None
    keywords: Optional[str] = None
    exclude_keywords: Optional[str] = None
    category_slug: Optional[str] = None
    location: Optional[str] = None
    min_price: Optional[Decimal] = None
    max_price: Optional[Decimal] = None
    price_drop_percent: Optional[int] = Field(default=None, ge=1, le=99)
    is_active: bool = True
    notify_telegram: bool = True
    notify_webpush: bool = True
    notify_ws: bool = True
    cooldown_seconds: int = 300


class AlertRuleCreate(AlertRuleBase):
    pass


class AlertRuleUpdate(BaseModel):
    name: Optional[str] = None
    is_active: Optional[bool] = None
    max_price: Optional[Decimal] = None
    min_price: Optional[Decimal] = None
    keywords: Optional[str] = None
    exclude_keywords: Optional[str] = None


class AlertRuleOut(AlertRuleBase):
    id: UUID
    user_id: UUID
    created_at: datetime

    class Config:
        from_attributes = True


class AlertMatchOut(BaseModel):
    id: int
    rule_id: UUID
    listing_id: UUID
    matched_at: datetime
    notified: bool
    payload: Optional[dict] = None

    class Config:
        from_attributes = True
