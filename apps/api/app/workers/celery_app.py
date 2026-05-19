from __future__ import annotations

from celery import Celery
from celery.schedules import crontab

from app.core.config import get_settings
from app.core.logging import configure_logging

configure_logging()
settings = get_settings()

celery_app = Celery(
    "caravan_hr",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=[
        "app.workers.sync_tasks",
        "app.workers.attendance_tasks",
        "app.workers.notification_tasks",
        "app.workers.personal_data_tasks",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_reject_on_worker_lost=True,
    task_default_retry_delay=60,
    task_max_retries=3,
    result_expires=3600,
    broker_transport_options={"visibility_timeout": 3600},
)

celery_app.conf.beat_schedule = {
    "sync-employees-every-15min": {
        "task": "app.workers.sync_tasks.sync_employees",
        "schedule": crontab(minute="*/15"),
        "options": {"expires": 840},
    },
    "sync-vacation-balances-every-15min": {
        "task": "app.workers.sync_tasks.sync_vacation_balances",
        "schedule": crontab(minute="*/15"),
        "options": {"expires": 840},
    },
    "sync-schedules-every-30min": {
        "task": "app.workers.sync_tasks.sync_schedules",
        "schedule": crontab(minute="*/30"),
        "options": {"expires": 1740},
    },
    "sync-departments-daily": {
        "task": "app.workers.sync_tasks.sync_departments",
        "schedule": crontab(hour=2, minute=0),
        "options": {"expires": 3540},
    },
    "sync-positions-daily": {
        "task": "app.workers.sync_tasks.sync_positions",
        "schedule": crontab(hour=2, minute=5),
        "options": {"expires": 3540},
    },
    "timesheet-builder-hourly": {
        "task": "app.workers.attendance_tasks.timesheet_builder",
        "schedule": crontab(minute=0),
        "options": {"expires": 3540},
    },
    "attendance-processor-continuous": {
        "task": "app.workers.attendance_tasks.attendance_processor",
        "schedule": crontab(minute="*/5"),
        "options": {"expires": 280},
    },
    # ---- Personal-data sync ----
    "sync-personal-data": {
        "task": "app.workers.sync_tasks.sync_personal_data_all",
        "schedule": crontab(minute="*/30"),
        "options": {"expires": 1740},
    },
    "sync-family-members": {
        "task": "app.workers.sync_tasks.sync_family_members_all",
        "schedule": crontab(hour="3", minute="30"),
        "options": {"expires": 3540},
    },
    "sync-bank-accounts": {
        "task": "app.workers.sync_tasks.sync_bank_accounts_all",
        "schedule": crontab(hour="3", minute="30"),
        "options": {"expires": 3540},
    },
    "sync-education": {
        "task": "app.workers.sync_tasks.sync_education_all",
        "schedule": crontab(day_of_week="0", hour="4"),
        "options": {"expires": 3540},
    },
}
