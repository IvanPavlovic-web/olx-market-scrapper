import uuid
from datetime import datetime
from decimal import Decimal
from sqlalchemy import (
    String,
    Text,
    Numeric,
    DateTime,
    Index,
    ForeignKey,
    BigInteger,
    Boolean,
    JSON,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class Category(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    source: Mapped[str] = mapped_column(String(32), index=True)
    slug: Mapped[str] = mapped_column(String(128), index=True)
    name: Mapped[str] = mapped_column(String(255))
    url: Mapped[str] = mapped_column(Text)
    parent_id: Mapped[int | None] = mapped_column(ForeignKey("categories.id"), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (Index("uq_cat_source_slug", "source", "slug", unique=True),)

class Listing(Base):
    __tablename__ = "listings"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source: Mapped[str] = mapped_column(String(32), index=True)
    external_id: Mapped[str] = mapped_column(String(128), index=True)
    url: Mapped[str] = mapped_column(Text)
    title: Mapped[str] = mapped_column(String(512))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    price: Mapped[Decimal | None] = mapped_column(Numeric(14, 2), nullable=True, index=True)
    currency: Mapped[str] = mapped_column(String(8), default="BAM", server_default="BAM")
    location: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    seller_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    images: Mapped[list | None] = mapped_column(JSON, nullable=True)
    attributes: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    category_id: Mapped[int | None] = mapped_column(ForeignKey("categories.id"), nullable=True)
    posted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    first_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    raw_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)

    category = relationship("Category")
    price_history = relationship("PriceHistory", back_populates="listing", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("source", "external_id", name="uq_listing_source_external"),
        Index("ix_listing_title_trgm", "title", postgresql_using="gin", postgresql_ops={"title": "gin_trgm_ops"}),
    )

class PriceHistory(Base):
    __tablename__ = "price_history"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    listing_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("listings.id", ondelete="CASCADE"), index=True)
    price: Mapped[Decimal | None] = mapped_column(Numeric(14, 2), nullable=True)
    currency: Mapped[str] = mapped_column(String(8), default="BAM", server_default="BAM")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    captured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)

    listing = relationship("Listing", back_populates="price_history")
