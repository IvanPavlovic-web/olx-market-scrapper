import uuid
from datetime import datetime
from decimal import Decimal
from sqlalchemy import (
    String, Text, Numeric, DateTime, ForeignKey, Boolean, JSON, func, Integer
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class AlertRule(Base):
    __tablename__ = "alert_rules"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(255))
    source: Mapped[str | None] = mapped_column(String(32), nullable=True)
    keywords: Mapped[str | None] = mapped_column(Text, nullable=True)
    exclude_keywords: Mapped[str | None] = mapped_column(Text, nullable=True)
    category_slug: Mapped[str | None] = mapped_column(String(128), nullable=True)
    location: Mapped[str | None] = mapped_column(String(128), nullable=True)
    min_price: Mapped[Decimal | None] = mapped_column(Numeric(14, 2), nullable=True)
    max_price: Mapped[Decimal | None] = mapped_column(Numeric(14, 2), nullable=True)
    price_drop_percent: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    notify_telegram: Mapped[bool] = mapped_column(Boolean, default=True)
    notify_webpush: Mapped[bool] = mapped_column(Boolean, default=True)
    notify_ws: Mapped[bool] = mapped_column(Boolean, default=True)
    cooldown_seconds: Mapped[int] = mapped_column(Integer, default=300)
    extra: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="alerts")
    matches = relationship("AlertMatch", back_populates="rule", cascade="all, delete-orphan")


class AlertMatch(Base):
    __tablename__ = "alert_matches"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    rule_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("alert_rules.id", ondelete="CASCADE"), index=True)
    listing_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("listings.id", ondelete="CASCADE"), index=True)
    matched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)
    notified: Mapped[bool] = mapped_column(Boolean, default=False)
    payload: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    rule = relationship("AlertRule", back_populates="matches")


class PushSubscription(Base):
    __tablename__ = "push_subscriptions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    endpoint: Mapped[str] = mapped_column(Text)
    p256dh: Mapped[str] = mapped_column(Text)
    auth: Mapped[str] = mapped_column(Text)
    user_agent: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="devices")


class ProxyNode(Base):
    __tablename__ = "proxy_nodes"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    url: Mapped[str] = mapped_column(Text, unique=True)
    is_healthy: Mapped[bool] = mapped_column(Boolean, default=True)
    last_checked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    fail_count: Mapped[int] = mapped_column(Integer, default=0)
    success_count: Mapped[int] = mapped_column(Integer, default=0)
