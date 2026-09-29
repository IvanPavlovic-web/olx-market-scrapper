"""initial schema + timescale

Revision ID: 0001
Revises:
Create Date: 2025-01-01
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.execute("CREATE EXTENSION IF NOT EXISTS timescaledb")
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')

    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(255), unique=True, nullable=False),
        sa.Column("username", sa.String(80), unique=True, nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("is_active", sa.Boolean, default=True),
        sa.Column("is_admin", sa.Boolean, default=False),
        sa.Column("telegram_chat_id", sa.String(64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_users_email", "users", ["email"])
    op.create_index("ix_users_username", "users", ["username"])

    op.create_table(
        "categories",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("source", sa.String(32), index=True),
        sa.Column("slug", sa.String(128), index=True),
        sa.Column("name", sa.String(255)),
        sa.Column("url", sa.Text),
        sa.Column("parent_id", sa.Integer, sa.ForeignKey("categories.id"), nullable=True),
        sa.Column("is_active", sa.Boolean, default=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_unique_constraint("uq_cat_source_slug", "categories", ["source", "slug"])

    op.create_table(
        "listings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("source", sa.String(32), index=True),
        sa.Column("external_id", sa.String(128), index=True),
        sa.Column("url", sa.Text),
        sa.Column("title", sa.String(512)),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("price", sa.Numeric(14, 2), nullable=True, index=True),
        sa.Column("currency", sa.String(8), server_default="BAM"),
        sa.Column("location", sa.String(128), nullable=True, index=True),
        sa.Column("seller_name", sa.String(255), nullable=True),
        sa.Column("images", sa.JSON, nullable=True),
        sa.Column("attributes", sa.JSON, nullable=True),
        sa.Column("category_id", sa.Integer, sa.ForeignKey("categories.id"), nullable=True),
        sa.Column("posted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("first_seen_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("is_active", sa.Boolean, default=True),
        sa.Column("raw_hash", sa.String(64), nullable=True),
    )
    op.create_unique_constraint("uq_listing_source_external", "listings", ["source", "external_id"])
    op.execute("CREATE INDEX ix_listing_title_trgm ON listings USING gin (title gin_trgm_ops)")

    op.create_table(
        "price_history",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("listing_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("listings.id", ondelete="CASCADE"), index=True),
        sa.Column("price", sa.Numeric(14, 2), nullable=True),
        sa.Column("currency", sa.String(8), server_default="BAM"),
        sa.Column("is_active", sa.Boolean, default=True),
        sa.Column("captured_at", sa.DateTime(timezone=True), server_default=sa.func.now(), index=True),
    )

    op.create_table(
        "alert_rules",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="CASCADE"), index=True),
        sa.Column("name", sa.String(255)),
        sa.Column("source", sa.String(32), nullable=True),
        sa.Column("keywords", sa.Text, nullable=True),
        sa.Column("exclude_keywords", sa.Text, nullable=True),
        sa.Column("category_slug", sa.String(128), nullable=True),
        sa.Column("location", sa.String(128), nullable=True),
        sa.Column("min_price", sa.Numeric(14, 2), nullable=True),
        sa.Column("max_price", sa.Numeric(14, 2), nullable=True),
        sa.Column("price_drop_percent", sa.Integer, nullable=True),
        sa.Column("is_active", sa.Boolean, default=True),
        sa.Column("notify_telegram", sa.Boolean, default=True),
        sa.Column("notify_webpush", sa.Boolean, default=True),
        sa.Column("notify_ws", sa.Boolean, default=True),
        sa.Column("cooldown_seconds", sa.Integer, default=300),
        sa.Column("extra", sa.JSON, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "alert_matches",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("rule_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("alert_rules.id", ondelete="CASCADE"), index=True),
        sa.Column("listing_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("listings.id", ondelete="CASCADE"), index=True),
        sa.Column("matched_at", sa.DateTime(timezone=True), server_default=sa.func.now(), index=True),
        sa.Column("notified", sa.Boolean, default=False),
        sa.Column("payload", sa.JSON, nullable=True),
    )

    op.create_table(
        "push_subscriptions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="CASCADE"), index=True),
        sa.Column("endpoint", sa.Text),
        sa.Column("p256dh", sa.Text),
        sa.Column("auth", sa.Text),
        sa.Column("user_agent", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "proxy_nodes",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("url", sa.Text, unique=True),
        sa.Column("is_healthy", sa.Boolean, default=True),
        sa.Column("last_checked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("fail_count", sa.Integer, default=0),
        sa.Column("success_count", sa.Integer, default=0),
    )


def downgrade():
    op.drop_table("proxy_nodes")
    op.drop_table("push_subscriptions")
    op.drop_table("alert_matches")
    op.drop_table("alert_rules")
    op.drop_table("price_history")
    op.drop_table("listings")
    op.drop_table("categories")
    op.drop_table("users")
