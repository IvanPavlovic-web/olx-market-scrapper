# OLX Monitor BiH

Real-time monitoring system for listings and prices on OLX.ba. FastAPI backend with async SQLAlchemy, Celery workers for scheduled scraping and alert evaluation, TimescaleDB (PostgreSQL 16) for persistence, Redis for the Celery broker and result backend, and a Next.js dashboard with live WebSocket alerts. Deployed through Docker Compose.

The application periodically scrapes popular OLX.ba categories, stores every listing with its price history, and evaluates user-defined alert rules (keywords, price range, location, price drop percentage). Matches are delivered in real time over WebSocket and optionally through Telegram.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend Framework | FastAPI 0.115, Uvicorn |
| ORM / Migrations | SQLAlchemy 2.0 (async, asyncpg), Alembic |
| Task Queue | Celery 5.4 (worker + beat), Flower 2.0 |
| Scraping | httpx (HTTP/2), tenacity retries, rotating proxy pool |
| Real-time | Native FastAPI WebSocket endpoint (`/ws`) |
| Authentication | JWT (`python-jose`), password hashing via `passlib` (bcrypt) |
| Database | TimescaleDB on PostgreSQL 16, `pg_trgm`, `uuid-ossp` |
| Cache / Broker | Redis 7 |
| Notifications | Telegram Bot API, WebSocket |
| Logging | structlog (JSON) |
| Frontend Framework | Next.js 16, React 18, TypeScript |
| Styling | Tailwind CSS 3 |
| Data Fetching | SWR, Axios |
| Charts | Recharts |
| UI Helpers | lucide-react, sonner (toasts), clsx, date-fns |
| Reverse Proxy | Nginx (optional config included) |
| Containerization | Docker, Docker Compose |
| Language | Python 3.11, TypeScript 5 |

---

## Features

- Scheduled scraping: Celery beat triggers a scrape of popular OLX.ba categories (cars, parts, phones, computers, furniture), staggered across the interval to avoid bursts.
- Listing storage with upsert: listings are keyed by `(source, external_id)`; title, price, and location changes are detected and flagged.
- Price history: every new listing and every price change is recorded in `price_history` for later analysis.
- Alert rules per user: keywords (all must match in title), exclude keywords, source, category, location, min / max price, price drop percentage, and per-rule cooldown.
- Real-time delivery: matched alerts are pushed to the user over WebSocket and shown in the live dashboard feed.
- Telegram notifications: formatted alert messages sent to the user's chat ID or to a default chat configured in `.env`.
- Proxy pool: optional rotating proxy list with cooldown on failing proxies.
- Automatic cleanup: listings not seen for 30 days are marked inactive every six hours.
- Dashboard: total / active listings, average price, live alert feed with price chart, latest listings, searchable listing browser, and alert management UI.
- JWT authentication with registration and login.
- Flower UI for inspecting Celery workers and tasks.
- Trigram index on listing titles for fast text lookups.

---

## Project Structure

```text
olx-monitor/
├── .env.example                          Environment variable template
├── docker-compose.yml                    Postgres, Redis, API, worker, beat, Flower, frontend
├── Makefile                              Shortcuts for common Docker commands
├── nginx/
│   └── nginx.conf                        Optional reverse proxy (API, WebSocket, frontend)
├── scripts/
│   ├── init_timescale.sql                Enables timescaledb, pg_trgm, uuid-ossp on first DB init
│   └── fix_backend.sh                    Rebuild and start all services
├── backend/
│   ├── Dockerfile                        Python 3.11 slim image
│   ├── requirements.txt
│   ├── alembic.ini
│   ├── alembic/
│   │   ├── env.py
│   │   ├── script.py.mako
│   │   └── versions/
│   │       └── 0001_initial.py           Initial schema
│   ├── tests/
│   └── app/
│       ├── main.py                       FastAPI app, routes, WebSocket endpoint
│       ├── api/
│       │   └── deps.py                   get_current_user dependency
│       ├── core/
│       │   ├── config.py                 Pydantic settings
│       │   ├── database.py               Async engine and session
│       │   └── logging.py                structlog configuration
│       ├── models/
│       │   ├── user.py
│       │   ├── listing.py                Category, Listing, PriceHistory
│       │   └── alert.py                  AlertRule, AlertMatch, PushSubscription, ProxyNode
│       ├── schemas/                      Pydantic request / response models
│       ├── scrapers/
│       │   ├── base.py                   BaseScraper with retries and proxy support
│       │   └── adapters/olx.py           OLX.ba API scraper
│       ├── services/
│       │   ├── scraper_service.py        Scrape, upsert, price history, alert dispatch
│       │   ├── notifications.py          Telegram notifier
│       │   └── proxy_pool.py             Round-robin proxy pool with cooldown
│       ├── utils/security.py             Password hashing and JWT helpers
│       ├── websocket/manager.py          Per-user WebSocket connection manager
│       └── workers/
│           ├── celery_app.py             Celery config and beat schedule
│           └── tasks.py                  Scrape, alert evaluation, cleanup tasks
└── frontend/
    ├── Dockerfile                        Node 20 image
    ├── package.json
    ├── next.config.js
    ├── tailwind.config.ts
    └── src/
        ├── app/
        │   ├── layout.tsx
        │   ├── page.tsx                  Landing page
        │   ├── login/page.tsx            Login and registration
        │   └── dashboard/
        │       ├── layout.tsx            Sidebar navigation
        │       ├── page.tsx              Overview, live feed, chart
        │       ├── listings/page.tsx     Search and filter listings
        │       ├── alerts/page.tsx       Create and delete alert rules
        │       └── settings/page.tsx
        ├── hooks/useWS.ts                WebSocket hook with ping
        ├── lib/
        │   ├── api.ts                    Axios instance and fetcher
        │   └── auth.ts                   Login, register, logout, cookie handling
        ├── styles/globals.css
        └── types/index.ts
```

---

## Setup and Installation

### Prerequisites

- Docker Desktop (Windows / macOS) or Docker Engine with Compose v2 (Linux)
- Git
- `make` (optional, for the shortcuts in the Makefile)

### Environment

Copy the example file and adjust values as needed:

```bash
cp .env.example .env
```

| Variable | Purpose |
|---|---|
| `APP_NAME` | Application title |
| `ENV` | Environment name (`development` / `production`) |
| `SECRET_KEY` | JWT signing key (change before any real deployment) |
| `JWT_ALGORITHM` | JWT algorithm (default `HS256`) |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token lifetime (default 1440) |
| `POSTGRES_USER` / `POSTGRES_PASSWORD` / `POSTGRES_DB` | Database credentials |
| `POSTGRES_HOST` / `POSTGRES_PORT` | Database host (`postgres` under Compose) and port |
| `REDIS_URL` | Redis connection string |
| `CELERY_BROKER_URL` | Celery broker (Redis DB 1) |
| `CELERY_RESULT_BACKEND` | Celery result backend (Redis DB 2) |
| `SCRAPER_CONCURRENCY` | Max concurrent scraper requests |
| `SCRAPER_TIMEOUT` | Request timeout in seconds |
| `SCRAPER_USER_AGENT` | User agent sent by the scraper |
| `PROXY_LIST` | Comma-separated proxy URLs (optional) |
| `SCRAPE_INTERVAL_SECONDS` | Scrape cycle interval (minimum effective value is 60) |
| `MAX_PAGES_PER_CATEGORY` | Pages fetched per category |
| `TELEGRAM_BOT_TOKEN` | Telegram bot token (optional) |
| `TELEGRAM_CHAT_ID` | Default Telegram chat for alerts (optional) |
| `NEXT_PUBLIC_API_URL` | API base URL used by the browser |
| `NEXT_PUBLIC_WS_URL` | WebSocket URL used by the browser |

### Build and start

```bash
docker compose up -d --build
```

or with the Makefile:

```bash
make up
```

On start, the API container retries `alembic upgrade head` until the database is ready, then launches Uvicorn with auto-reload. The worker consumes the `scrape`, `alerts`, `default`, and `celery` queues, and beat schedules the periodic tasks.

### Useful commands

```bash
make logs        # follow logs of all services
make ps          # service status
make shell       # bash inside the API container
make migrate     # apply migrations
make revision m="add new column"   # autogenerate a migration
make restart     # restart api, worker, beat, frontend
make down        # stop services
make clean       # stop services and wipe ./data/postgres and ./data/redis
```

### Access

| Service | URL |
|---|---|
| Frontend dashboard | `http://localhost:3000` |
| API | `http://localhost:8000` |
| API docs (Swagger) | `http://localhost:8000/docs` |
| Health check | `http://localhost:8000/health` |
| Flower (Celery monitor) | `http://localhost:5555` |

Register a new account on the login page, create an alert rule, and wait for the next scrape cycle.

### Data persistence

PostgreSQL and Redis data are stored on the host in `./data/postgres` and `./data/redis`. `make clean` removes them.

---

## Scraping and Alert Flow

1. Celery beat runs `scrape_all_categories` every `max(SCRAPE_INTERVAL_SECONDS, 60)` seconds.
2. One `scrape_category_task` per category is scheduled with a staggered countdown.
3. The OLX adapter queries `api.olx.ba/search` for the category and normalizes the records into `ScrapedListing` objects.
4. `ScraperService` upserts listings, writes a `price_history` row on new listings or price changes, and returns the IDs of changed listings.
5. Each changed listing is dispatched to `evaluate_alerts_for_listing` on the `alerts` queue.
6. Every active rule is checked against the listing. A match is stored in `alert_matches`, respecting the rule's cooldown.
7. Notifications are sent through Telegram and WebSocket, depending on the rule's flags.

---

## API Reference

Authenticated endpoints require `Authorization: Bearer <token>`.

### System

| Method | Endpoint | Description |
|---|---|---|
| GET | `/health` | Database connectivity check |

### Authentication

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/auth/register` | Create an account and receive a token |
| POST | `/api/auth/login` | Log in and receive a token |

### Listings

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/listings?q=&max_price=&limit=` | List active listings, newest first (limit 1 to 200) |
| GET | `/api/listings/stats/summary` | Total, active count, and average price |

### Alerts

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/alerts` | List the current user's alert rules |
| POST | `/api/alerts` | Create an alert rule |
| DELETE | `/api/alerts/{rule_id}` | Delete an alert rule |

### WebSocket

| Endpoint | Purpose |
|---|---|
| `ws://<host>/ws?token=<jwt>` | Real-time alert events for the authenticated user |

Alert event payload:

```json
{
  "type": "alert",
  "rule_name": "Passat B8 under 20k",
  "listing": {
    "title": "VW Passat B8 2.0 TDI",
    "price": "19500.00",
    "currency": "BAM",
    "url": "https://olx.ba/artikal/12345678",
    "location": "Banja Luka"
  }
}
```

### Alert rule fields

| Field | Description |
|---|---|
| `name` | Rule name shown in notifications |
| `source` | Restrict to a source (currently `olx`) |
| `keywords` | Comma-separated; all must appear in the title |
| `exclude_keywords` | Comma-separated; any match rejects the listing |
| `category_slug` | Restrict to a category slug |
| `location` | Case-insensitive substring match on location |
| `min_price` / `max_price` | Price bounds (listings without a price never match a bounded rule) |
| `price_drop_percent` | Minimum drop versus the previous recorded price (1 to 99) |
| `cooldown_seconds` | Minimum time before the same listing can re-trigger the rule |
| `notify_telegram` / `notify_ws` | Delivery channels |

---

## Security & Architecture Considerations

- Passwords are hashed with bcrypt through `passlib`. JWTs are signed with `SECRET_KEY`; the default value in `.env.example` must be replaced before any real deployment.
- Alert endpoints are scoped by `user_id`, so users can only read and delete their own rules.
- CORS is restricted to `http://localhost:3000` and `http://127.0.0.1:3000`. Update the allowed origins in `backend/app/main.py` for other environments.
- The frontend stores the JWT and user object in JavaScript-readable cookies, and the WebSocket token is passed in the query string. This is acceptable for local development; for production consider HttpOnly cookies and a short-lived WebSocket ticket.
- Registration is open. Add invitation codes or an admin approval step if the instance is publicly reachable.
- `docker-compose.yml` publishes Postgres (5432), Redis (6379), and Flower (5555) on the host. Remove these port mappings or firewall them outside local development, and protect Flower with authentication.
- The API runs with `--reload` and source directories are bind-mounted into the containers. This is a development setup; use a production Uvicorn / Gunicorn command and baked images for deployment.
- Telegram alerts use the per-user `telegram_chat_id` when set, otherwise the default `TELEGRAM_CHAT_ID`. There is currently no API endpoint for users to set their own chat ID.
- The `notify_webpush` flag and the `push_subscriptions` table exist in the schema, but Web Push delivery is not implemented yet.
- Scraping depends on the public OLX.ba API and its terms of use. Keep request rates conservative (`SCRAPE_INTERVAL_SECONDS`, `MAX_PAGES_PER_CATEGORY`) and review the site's terms before running this against production traffic.
- Timescale is enabled at the extension level, but tables are regular PostgreSQL tables. Converting `price_history` to a hypertable is a possible future optimization.
- The included `nginx/nginx.conf` proxies `/api/`, `/ws`, and the frontend, but the Nginx service is not part of the current Compose file.

---

## License

Proprietary. Copyright (c) OLX Monitor BiH contributors. All rights reserved. Redistribution or commercial use without prior written permission is prohibited.
