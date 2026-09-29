from datetime import datetime
from decimal import Decimal
from typing import Any, Optional
from uuid import UUID
from pydantic import BaseModel


class ListingOut(BaseModel):
    id: UUID
    source: str
    external_id: str
    url: str
    title: str
    price: Optional[Decimal] = None
    currency: str = "BAM"
    location: Optional[str] = None
    images: Optional[Any] = None
    attributes: Optional[Any] = None
    first_seen_at: datetime
    last_seen_at: datetime

    class Config:
        from_attributes = True


class PricePoint(BaseModel):
    captured_at: datetime
    price: Optional[Decimal]


class ListingDetail(ListingOut):
    description: Optional[str] = None
    seller_name: Optional[str] = None
    posted_at: Optional[datetime] = None
    history: list[PricePoint] = []
