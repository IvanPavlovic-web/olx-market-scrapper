from celery import Celery
from celery.schedules import crontab
from app.core.config import settings

celery_app = Celery(
    "olx_monitor",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.workers.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    task_default_queue="default",
    timezone="Europe/Sarajevo",
    enable_utc=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    broker_connection_retry_on_startup=True,
    task_routes={
        "app.workers.tasks.scrape_category_task": {"queue": "scrape"},
        "app.workers.tasks.evaluate_alerts_for_listing": {"queue": "alerts"},
    },
    beat_schedule={
        "scrape-popular-categories": {
            "task": "app.workers.tasks.scrape_all_categories",
            "schedule": max(settings.SCRAPE_INTERVAL_SECONDS, 60),
        },
        "cleanup-stale-listings": {
            "task": "app.workers.tasks.cleanup_stale_listings",
            "schedule": crontab(minute=0, hour="*/6"),
        },
    },
)
