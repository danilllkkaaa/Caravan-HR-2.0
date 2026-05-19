from __future__ import annotations

import asyncio
import json
import uuid
from datetime import UTC, date, datetime

import structlog

from app.core.config import get_settings
from app.workers.celery_app import celery_app

log = structlog.get_logger(__name__)
settings = get_settings()

STREAM_KEY = settings.hikvision_attendance_stream
CONSUMER_GROUP = "attendance_processors"
CONSUMER_NAME = "worker-1"
BATCH_SIZE = 100


async def _ensure_consumer_group(redis) -> None:
    try:
        await redis.xgroup_create(STREAM_KEY, CONSUMER_GROUP, id="0", mkstream=True)
    except Exception:
        pass  # Group already exists


async def _resolve_employee_id(
    session, hikvision_person_id: str
) -> uuid.UUID | None:
    """Resolve Hikvision person ID to internal employee ID."""


    # Look up last matched mapping or use external_id_1c as fallback
    # TODO: Add a mapping table or field for hikvision_person_id -> employee when integration spec is confirmed
    return None


async def _process_attendance_batch(messages: list) -> int:
    from app.infrastructure.database import get_session_factory
    from app.infrastructure.models import AttendanceEvent

    processed = 0

    async with get_session_factory()() as session:
        for message_id, fields in messages:
            try:
                raw_data = fields.get("data", "{}")
                payload = json.loads(raw_data)

                person_id = str(payload.get("personId", ""))
                event_time_str = payload.get("time", "")
                event_type_raw = payload.get("eventType", "")
                device_id = str(payload.get("deviceId", ""))

                try:
                    event_at = datetime.fromisoformat(event_time_str)
                    if event_at.tzinfo is None:
                        event_at = event_at.replace(tzinfo=UTC)
                except (ValueError, TypeError):
                    event_at = datetime.now(UTC)

                event_type = "entry" if "entry" in event_type_raw.lower() else "exit"

                employee_id = await _resolve_employee_id(session, person_id)

                event = AttendanceEvent(
                    employee_id=employee_id,
                    hikvision_person_id=person_id,
                    event_at=event_at,
                    event_type=event_type,
                    device_id=device_id,
                    raw_payload=payload,
                    processed=True,
                )
                session.add(event)
                processed += 1

            except Exception as e:
                log.warning(
                    "Failed to process attendance message",
                    message_id=message_id,
                    error=str(e),
                )

        await session.commit()

    return processed


async def _run_attendance_processor() -> dict[str, int]:
    from app.infrastructure.database import get_redis

    redis = get_redis()
    await _ensure_consumer_group(redis)

    messages_raw = await redis.xreadgroup(
        groupname=CONSUMER_GROUP,
        consumername=CONSUMER_NAME,
        streams={STREAM_KEY: ">"},
        count=BATCH_SIZE,
        block=100,
    )

    if not messages_raw:
        return {"processed": 0}

    all_messages = []
    message_ids = []
    for stream_name, stream_messages in messages_raw:
        for message_id, fields in stream_messages:
            all_messages.append((message_id, fields))
            message_ids.append(message_id)

    processed = await _process_attendance_batch(all_messages)

    if message_ids:
        await redis.xack(STREAM_KEY, CONSUMER_GROUP, *message_ids)

    return {"processed": processed, "total_messages": len(all_messages)}


async def _run_timesheet_builder() -> dict[str, int]:
    """Build/update timesheet entries from attendance events."""
    from sqlalchemy import select

    from app.infrastructure.database import get_session_factory
    from app.infrastructure.models import AttendanceEvent, TimesheetEntry

    built = 0
    today = date.today()

    async with get_session_factory()() as session:
        stmt = (
            select(AttendanceEvent)
            .where(
                AttendanceEvent.employee_id.isnot(None),
                AttendanceEvent.event_at >= datetime(today.year, today.month, today.day, tzinfo=UTC),
            )
            .order_by(AttendanceEvent.employee_id, AttendanceEvent.event_at)
        )
        result = await session.execute(stmt)
        events = result.scalars().all()

        by_employee: dict[uuid.UUID, list[AttendanceEvent]] = {}
        for event in events:
            if event.employee_id not in by_employee:
                by_employee[event.employee_id] = []
            by_employee[event.employee_id].append(event)

        for employee_id, emp_events in by_employee.items():
            entry_events = [e for e in emp_events if e.event_type == "entry"]
            exit_events = [e for e in emp_events if e.event_type == "exit"]

            first_entry = min((e.event_at for e in entry_events), default=None)
            last_exit = max((e.event_at for e in exit_events), default=None)

            worked_minutes = 0
            if first_entry and last_exit and last_exit > first_entry:
                worked_minutes = int((last_exit - first_entry).total_seconds() / 60)

            stmt = select(TimesheetEntry).where(
                TimesheetEntry.employee_id == employee_id,
                TimesheetEntry.date == today,
            )
            ts_result = await session.execute(stmt)
            entry = ts_result.scalar_one_or_none()

            if entry is None:
                entry = TimesheetEntry(
                    id=uuid.uuid4(),
                    employee_id=employee_id,
                    date=today,
                    first_entry_at=first_entry,
                    last_exit_at=last_exit,
                    worked_minutes=worked_minutes,
                    status="work",
                )
                session.add(entry)
            else:
                if first_entry:
                    entry.first_entry_at = first_entry
                if last_exit:
                    entry.last_exit_at = last_exit
                entry.worked_minutes = worked_minutes

            built += 1

        await session.commit()

    return {"built": built, "date": today.isoformat()}


@celery_app.task(name="app.workers.attendance_tasks.attendance_processor", bind=True)
def attendance_processor(self) -> dict[str, int]:
    log.info("Running attendance processor")
    try:
        result = asyncio.run(_run_attendance_processor())
        if result.get("processed", 0) > 0:
            log.info("Attendance events processed", **result)
        return result
    except Exception as exc:
        log.exception("attendance_processor failed", error=str(exc))
        raise self.retry(exc=exc, countdown=10, max_retries=5)


@celery_app.task(name="app.workers.attendance_tasks.timesheet_builder", bind=True)
def timesheet_builder(self) -> dict[str, int]:
    log.info("Running timesheet builder")
    try:
        result = asyncio.run(_run_timesheet_builder())
        log.info("Timesheet builder completed", **result)
        return result
    except Exception as exc:
        log.exception("timesheet_builder failed", error=str(exc))
        raise self.retry(exc=exc, countdown=60, max_retries=3)
