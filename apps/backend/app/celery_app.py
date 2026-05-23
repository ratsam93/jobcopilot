from __future__ import annotations

from celery import Celery

from apps.backend.app.config import settings


celery_app = Celery(
    "jobcopilot",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["apps.backend.app.worker_tasks"],
)

celery_app.conf.update(
    task_track_started=True,
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    broker_connection_retry_on_startup=True,
)
