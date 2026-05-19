from __future__ import annotations

import asyncio
import uuid
from typing import Any

import structlog

from app.core.config import get_settings
from app.workers.celery_app import celery_app

log = structlog.get_logger(__name__)
settings = get_settings()


async def _send_push_notification_async(
    employee_id: str,
    title: str,
    body: str,
    data: dict[str, Any] | None,
) -> bool:
    """Send push notification via Firebase Cloud Messaging."""
    if not settings.firebase_credentials_path:
        log.debug("Firebase not configured, skipping push notification")
        return False

    # TODO: Initialize firebase-admin SDK with settings.firebase_credentials_path
    # and call messaging.send() when FCM integration is set up.
    # Example structure:
    # import firebase_admin
    # from firebase_admin import credentials, messaging
    # cred = credentials.Certificate(settings.firebase_credentials_path)
    # firebase_admin.initialize_app(cred)
    # message = messaging.Message(
    #     notification=messaging.Notification(title=title, body=body),
    #     data=data or {},
    #     token=device_token,
    # )
    # messaging.send(message)
    log.warning(
        "Firebase push not yet implemented - notification stored in DB only",
        employee_id=employee_id,
    )
    return False


async def _create_db_notification(
    employee_id: str,
    notification_type: str,
    title: str,
    body: str,
    payload: dict[str, Any] | None,
) -> None:
    from app.infrastructure.database import get_session_factory
    from app.infrastructure.repositories.notification import NotificationRepository

    async with get_session_factory()() as session:
        repo = NotificationRepository(session)
        await repo.create(
            uuid.UUID(employee_id),
            {
                "type": notification_type,
                "title": title,
                "body": body,
                "payload": payload,
            },
        )
        await session.commit()


@celery_app.task(
    name="app.workers.notification_tasks.send_push_notification",
    bind=True,
    max_retries=3,
)
def send_push_notification(
    self,
    employee_id: str,
    notification_type: str,
    title: str,
    body: str,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Send push notification to employee and store in DB."""
    log.info(
        "Sending push notification",
        employee_id=employee_id,
        type=notification_type,
    )
    try:
        asyncio.run(_create_db_notification(employee_id, notification_type, title, body, payload))

        push_sent = asyncio.run(
            _send_push_notification_async(employee_id, title, body, payload)
        )

        return {
            "employee_id": employee_id,
            "db_stored": True,
            "push_sent": push_sent,
        }
    except Exception as exc:
        log.exception("send_push_notification failed", error=str(exc))
        raise self.retry(exc=exc, countdown=30)


@celery_app.task(
    name="app.workers.notification_tasks.send_vacation_approved",
    bind=True,
)
def send_vacation_approved(
    self,
    employee_id: str,
    request_id: str,
    start_date: str,
    end_date: str,
    days_count: int,
) -> dict[str, Any]:
    return send_push_notification.apply(
        args=[
            employee_id,
            "approved",
            "Vacation Approved",
            f"Your vacation request from {start_date} to {end_date} ({days_count} days) has been approved.",
            {"vacation_request_id": request_id},
        ]
    ).get()


@celery_app.task(
    name="app.workers.notification_tasks.send_vacation_rejected",
    bind=True,
)
def send_vacation_rejected(
    self,
    employee_id: str,
    request_id: str,
    comment: str,
) -> dict[str, Any]:
    return send_push_notification.apply(
        args=[
            employee_id,
            "rejected",
            "Vacation Request Rejected",
            f"Your vacation request has been rejected. Reason: {comment}",
            {"vacation_request_id": request_id},
        ]
    ).get()
