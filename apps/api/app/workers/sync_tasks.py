from __future__ import annotations

import asyncio
import hashlib
import json
from typing import Any

import httpx
import sentry_sdk
import structlog
from celery.exceptions import MaxRetriesExceededError

from app.core.config import get_settings
from app.workers.celery_app import celery_app

log = structlog.get_logger(__name__)
settings = get_settings()

# NOTE: The actual 1C API endpoint paths below are placeholders.
# Replace with real 1C:Enterprise HTTP service routes when available.
OC_ENDPOINTS = {
    "employees": "employees",           # TODO: replace with actual 1C route
    "departments": "departments",       # TODO: replace with actual 1C route
    "positions": "positions",           # TODO: replace with actual 1C route
    "vacation_balances": "vacationBalances",  # TODO: replace with actual 1C route
    "schedules": "workSchedules",       # TODO: replace with actual 1C route
    # Personal-data endpoints (placeholders — replace when 1C API is confirmed)
    "personal_data": "personalData",
    "family_members": "familyMembers",
    "bank_accounts": "bankAccounts",
    "education": "educationRecords",
}


def _get_http_client() -> httpx.AsyncClient:
    return httpx.AsyncClient(
        base_url=settings.oc_base_url,
        auth=(settings.oc_username, settings.oc_password),
        timeout=settings.oc_timeout,
        headers={"Accept": "application/json"},
    )


async def _fetch_from_1c(endpoint: str) -> list[dict[str, Any]]:
    async with _get_http_client() as client:
        response = await client.get(endpoint)
        response.raise_for_status()
        return response.json()


def _compute_hash(data: dict[str, Any]) -> str:
    serialized = json.dumps(data, sort_keys=True, default=str)
    return hashlib.sha256(serialized.encode()).hexdigest()[:64]


async def _run_sync_employees() -> dict[str, int]:

    from app.infrastructure.database import get_session_factory
    from app.infrastructure.repositories.employee import EmployeeRepository

    records = await _fetch_from_1c(OC_ENDPOINTS["employees"])
    updated = created = skipped = 0

    async with get_session_factory()() as session:
        repo = EmployeeRepository(session)
        for record in records:
            sync_hash = _compute_hash(record)
            try:
                await repo.upsert_from_1c({**record, "sync_hash": sync_hash})
                updated += 1
            except Exception as e:
                log.warning("Failed to upsert employee", error=str(e), record=record)
                skipped += 1
        await session.commit()

    return {"updated": updated, "created": created, "skipped": skipped}


async def _run_sync_departments() -> dict[str, int]:
    from sqlalchemy import select

    from app.infrastructure.database import get_session_factory
    from app.infrastructure.models import Department

    records = await _fetch_from_1c(OC_ENDPOINTS["departments"])
    upserted = 0

    async with get_session_factory()() as session:
        for record in records:
            stmt = select(Department).where(
                Department.external_id_1c == record.get("external_id_1c")
            )
            result = await session.execute(stmt)
            dept = result.scalar_one_or_none()
            if dept is None:
                import uuid

                dept = Department(
                    id=uuid.uuid4(),
                    external_id_1c=record["external_id_1c"],
                    name=record.get("name", ""),
                    parent_id=None,
                )
                session.add(dept)
            else:
                dept.name = record.get("name", dept.name)
            upserted += 1
        await session.commit()

    return {"upserted": upserted}


async def _run_sync_positions() -> dict[str, int]:
    from sqlalchemy import select

    from app.infrastructure.database import get_session_factory
    from app.infrastructure.models import Position

    records = await _fetch_from_1c(OC_ENDPOINTS["positions"])
    upserted = 0

    async with get_session_factory()() as session:
        for record in records:
            stmt = select(Position).where(
                Position.external_id_1c == record.get("external_id_1c")
            )
            result = await session.execute(stmt)
            pos = result.scalar_one_or_none()
            if pos is None:
                import uuid

                pos = Position(
                    id=uuid.uuid4(),
                    external_id_1c=record["external_id_1c"],
                    name=record.get("name", ""),
                )
                session.add(pos)
            else:
                pos.name = record.get("name", pos.name)
            upserted += 1
        await session.commit()

    return {"upserted": upserted}


async def _run_sync_vacation_balances() -> dict[str, int]:
    from decimal import Decimal

    from sqlalchemy import select

    from app.infrastructure.database import get_session_factory
    from app.infrastructure.models import VacationBalance

    records = await _fetch_from_1c(OC_ENDPOINTS["vacation_balances"])
    upserted = 0
    import uuid

    async with get_session_factory()() as session:
        for record in records:
            employee_id = record.get("employee_id")
            year = record.get("year")
            if not employee_id or not year:
                continue

            stmt = select(VacationBalance).where(
                VacationBalance.employee_id == uuid.UUID(employee_id),
                VacationBalance.year == int(year),
            )
            result = await session.execute(stmt)
            bal = result.scalar_one_or_none()

            total_days = Decimal(str(record.get("total_days", 0)))
            used_days = Decimal(str(record.get("used_days", 0)))

            if bal is None:
                bal = VacationBalance(
                    id=uuid.uuid4(),
                    employee_id=uuid.UUID(employee_id),
                    year=int(year),
                    total_days=total_days,
                    used_days=used_days,
                    sync_source="1c",
                )
                session.add(bal)
            else:
                bal.total_days = total_days
                bal.used_days = used_days
                bal.sync_source = "1c"
            upserted += 1
        await session.commit()

    return {"upserted": upserted}


@celery_app.task(name="app.workers.sync_tasks.sync_employees", bind=True, max_retries=3)
def sync_employees(self) -> dict[str, int]:
    log.info("Starting sync_employees task")
    try:
        result = asyncio.run(_run_sync_employees())
        log.info("sync_employees completed", **result)
        return result
    except Exception as exc:
        log.exception("sync_employees failed", error=str(exc))
        try:
            raise self.retry(exc=exc, countdown=60)
        except MaxRetriesExceededError:
            sentry_sdk.capture_exception(exc)
            raise


@celery_app.task(name="app.workers.sync_tasks.sync_vacation_balances", bind=True, max_retries=3)
def sync_vacation_balances(self) -> dict[str, int]:
    log.info("Starting sync_vacation_balances task")
    try:
        result = asyncio.run(_run_sync_vacation_balances())
        log.info("sync_vacation_balances completed", **result)
        return result
    except Exception as exc:
        log.exception("sync_vacation_balances failed", error=str(exc))
        try:
            raise self.retry(exc=exc, countdown=60)
        except MaxRetriesExceededError:
            sentry_sdk.capture_exception(exc)
            raise


@celery_app.task(name="app.workers.sync_tasks.sync_departments", bind=True, max_retries=3)
def sync_departments(self) -> dict[str, int]:
    log.info("Starting sync_departments task")
    try:
        result = asyncio.run(_run_sync_departments())
        log.info("sync_departments completed", **result)
        return result
    except Exception as exc:
        log.exception("sync_departments failed", error=str(exc))
        try:
            raise self.retry(exc=exc, countdown=300)
        except MaxRetriesExceededError:
            sentry_sdk.capture_exception(exc)
            raise


@celery_app.task(name="app.workers.sync_tasks.sync_positions", bind=True, max_retries=3)
def sync_positions(self) -> dict[str, int]:
    log.info("Starting sync_positions task")
    try:
        result = asyncio.run(_run_sync_positions())
        log.info("sync_positions completed", **result)
        return result
    except Exception as exc:
        log.exception("sync_positions failed", error=str(exc))
        try:
            raise self.retry(exc=exc, countdown=300)
        except MaxRetriesExceededError:
            sentry_sdk.capture_exception(exc)
            raise


@celery_app.task(name="app.workers.sync_tasks.sync_schedules", bind=True, max_retries=3)
def sync_schedules(self) -> dict[str, Any]:
    """Sync work schedules from 1C. Endpoint to be configured."""
    log.info("Starting sync_schedules task")
    # TODO: Implement when 1C work schedule API endpoint is confirmed
    return {"status": "not_implemented"}


# ---------------------------------------------------------------------------
# Personal-data sync tasks
# ---------------------------------------------------------------------------


async def _run_sync_personal_data_all() -> dict[str, int]:
    """Sync PersonalData for all active employees from 1C."""

    from app.infrastructure.database import get_session_factory
    from app.infrastructure.repositories.personal_data import PersonalDataRepository

    records = await _fetch_from_1c(OC_ENDPOINTS["personal_data"])
    updated = skipped = 0

    async with get_session_factory()() as session:
        repo = PersonalDataRepository(session)
        for record in records:
            employee_id_str = record.get("employee_id")
            if not employee_id_str:
                skipped += 1
                continue
            try:
                import uuid as _uuid

                employee_id = _uuid.UUID(employee_id_str)
                sync_hash = _compute_hash(record)
                data = {
                    k: v
                    for k, v in record.items()
                    if k not in ("employee_id",)
                }
                data["sync_hash"] = sync_hash
                await repo.upsert_personal_data(employee_id, data, source="1c")
                updated += 1
            except Exception as exc:
                log.warning(
                    "Failed to upsert personal_data from 1C",
                    error=str(exc),
                    employee_id=employee_id_str,
                )
                skipped += 1
        await session.commit()

    return {"updated": updated, "skipped": skipped}


async def _run_sync_personal_data_employee(employee_id: str) -> dict[str, int]:
    """Sync PersonalData for a single employee from 1C."""
    import uuid as _uuid

    from app.infrastructure.database import get_session_factory
    from app.infrastructure.repositories.personal_data import PersonalDataRepository

    emp_uuid = _uuid.UUID(employee_id)
    records = await _fetch_from_1c(f"{OC_ENDPOINTS['personal_data']}/{employee_id}")
    if not records:
        return {"updated": 0, "skipped": 1}

    record = records[0] if isinstance(records, list) else records
    sync_hash = _compute_hash(record)
    data = {k: v for k, v in record.items() if k != "employee_id"}
    data["sync_hash"] = sync_hash

    async with get_session_factory()() as session:
        repo = PersonalDataRepository(session)
        await repo.upsert_personal_data(emp_uuid, data, source="1c")
        await session.commit()

    return {"updated": 1, "skipped": 0}


async def _run_sync_family_members_all() -> dict[str, int]:
    """Sync family members for all employees from 1C."""
    from app.core.encryption import encrypt_field
    from app.infrastructure.database import get_session_factory
    from app.infrastructure.repositories.personal_data import PersonalDataRepository

    records = await _fetch_from_1c(OC_ENDPOINTS["family_members"])
    updated = skipped = 0

    async with get_session_factory()() as session:
        repo = PersonalDataRepository(session)
        for record in records:
            employee_id_str = record.get("employee_id")
            if not employee_id_str:
                skipped += 1
                continue
            try:
                import uuid as _uuid

                employee_id = _uuid.UUID(employee_id_str)
                data = {k: v for k, v in record.items() if k not in ("employee_id",)}
                # Encrypt IIN before storing
                if data.get("iin"):
                    data["iin_encrypted"] = encrypt_field(str(data.pop("iin")))
                else:
                    data.pop("iin", None)
                    data.setdefault("iin_encrypted", None)
                data["employee_id"] = employee_id
                data.setdefault("data_source", "1c")
                await repo.add_family_member(data)
                updated += 1
            except Exception as exc:
                log.warning(
                    "Failed to upsert family_member from 1C",
                    error=str(exc),
                    employee_id=employee_id_str,
                )
                skipped += 1
        await session.commit()

    return {"updated": updated, "skipped": skipped}


async def _run_sync_bank_accounts_all() -> dict[str, int]:
    """Sync bank accounts for all employees from 1C."""
    from app.core.encryption import encrypt_field
    from app.infrastructure.database import get_session_factory
    from app.infrastructure.repositories.personal_data import PersonalDataRepository

    records = await _fetch_from_1c(OC_ENDPOINTS["bank_accounts"])
    updated = skipped = 0

    async with get_session_factory()() as session:
        repo = PersonalDataRepository(session)
        for record in records:
            employee_id_str = record.get("employee_id")
            if not employee_id_str:
                skipped += 1
                continue
            try:
                import uuid as _uuid

                employee_id = _uuid.UUID(employee_id_str)
                data = {k: v for k, v in record.items() if k != "employee_id"}
                if data.get("account_number"):
                    data["account_number_encrypted"] = encrypt_field(
                        str(data.pop("account_number"))
                    )
                data["employee_id"] = employee_id
                data.setdefault("data_source", "1c")
                await repo.add_bank_account(data)
                updated += 1
            except Exception as exc:
                log.warning(
                    "Failed to upsert bank_account from 1C",
                    error=str(exc),
                    employee_id=employee_id_str,
                )
                skipped += 1
        await session.commit()

    return {"updated": updated, "skipped": skipped}


async def _run_sync_education_all() -> dict[str, int]:
    """Sync education records for all employees from 1C."""
    from app.infrastructure.database import get_session_factory
    from app.infrastructure.repositories.personal_data import PersonalDataRepository

    records = await _fetch_from_1c(OC_ENDPOINTS["education"])
    updated = skipped = 0

    async with get_session_factory()() as session:
        repo = PersonalDataRepository(session)
        for record in records:
            employee_id_str = record.get("employee_id")
            if not employee_id_str:
                skipped += 1
                continue
            try:
                import uuid as _uuid

                employee_id = _uuid.UUID(employee_id_str)
                data = {k: v for k, v in record.items() if k != "employee_id"}
                data["employee_id"] = employee_id
                data.setdefault("data_source", "1c")
                await repo.add_education_record(data)
                updated += 1
            except Exception as exc:
                log.warning(
                    "Failed to upsert education_record from 1C",
                    error=str(exc),
                    employee_id=employee_id_str,
                )
                skipped += 1
        await session.commit()

    return {"updated": updated, "skipped": skipped}


async def _send_change_request_email_async(request_id: str) -> None:
    """Send HR notification email about a new change request."""
    import uuid as _uuid

    from app.infrastructure.database import get_session_factory
    from app.infrastructure.repositories.personal_data import ChangeRequestRepository

    async with get_session_factory()() as session:
        repo = ChangeRequestRepository(session)
        cr = await repo.get(_uuid.UUID(request_id))
        if cr is None:
            log.warning("ChangeRequest not found for email", request_id=request_id)
            return

        # TODO: integrate with actual SMTP / SendGrid when email service is configured.
        # The placeholder below logs the intent.
        log.info(
            "Would send change-request email",
            to=cr.hr_email,
            section=cr.section,
            field=cr.field_name,
            employee_id=str(cr.employee_id),
            request_id=request_id,
        )


# ---------------------------------------------------------------------------
# Celery task wrappers
# ---------------------------------------------------------------------------


@celery_app.task(
    name="app.workers.sync_tasks.sync_personal_data_all",
    bind=True,
    max_retries=3,
)
def sync_personal_data_all(self) -> dict[str, int]:
    """Sync PersonalData for all active employees from 1C."""
    log.info("Starting sync_personal_data_all task")
    try:
        result = asyncio.run(_run_sync_personal_data_all())
        log.info("sync_personal_data_all completed", **result)
        return result
    except Exception as exc:
        log.exception("sync_personal_data_all failed", error=str(exc))
        try:
            raise self.retry(exc=exc, countdown=60)
        except MaxRetriesExceededError:
            sentry_sdk.capture_exception(exc)
            raise


@celery_app.task(
    name="app.workers.sync_tasks.sync_personal_data_employee",
    bind=True,
    max_retries=3,
)
def sync_personal_data_employee(self, employee_id: str) -> dict[str, int]:
    """Sync PersonalData for a single employee."""
    log.info("Starting sync_personal_data_employee", employee_id=employee_id)
    try:
        result = asyncio.run(_run_sync_personal_data_employee(employee_id))
        log.info("sync_personal_data_employee completed", employee_id=employee_id, **result)
        return result
    except Exception as exc:
        log.exception(
            "sync_personal_data_employee failed",
            employee_id=employee_id,
            error=str(exc),
        )
        try:
            raise self.retry(exc=exc, countdown=60)
        except MaxRetriesExceededError:
            sentry_sdk.capture_exception(exc)
            raise


@celery_app.task(
    name="app.workers.sync_tasks.sync_family_members_all",
    bind=True,
    max_retries=3,
)
def sync_family_members_all(self) -> dict[str, int]:
    """Sync family_members from 1C for all employees."""
    log.info("Starting sync_family_members_all task")
    try:
        result = asyncio.run(_run_sync_family_members_all())
        log.info("sync_family_members_all completed", **result)
        return result
    except Exception as exc:
        log.exception("sync_family_members_all failed", error=str(exc))
        try:
            raise self.retry(exc=exc, countdown=120)
        except MaxRetriesExceededError:
            sentry_sdk.capture_exception(exc)
            raise


@celery_app.task(
    name="app.workers.sync_tasks.sync_bank_accounts_all",
    bind=True,
    max_retries=3,
)
def sync_bank_accounts_all(self) -> dict[str, int]:
    """Sync bank_accounts from 1C for all employees."""
    log.info("Starting sync_bank_accounts_all task")
    try:
        result = asyncio.run(_run_sync_bank_accounts_all())
        log.info("sync_bank_accounts_all completed", **result)
        return result
    except Exception as exc:
        log.exception("sync_bank_accounts_all failed", error=str(exc))
        try:
            raise self.retry(exc=exc, countdown=120)
        except MaxRetriesExceededError:
            sentry_sdk.capture_exception(exc)
            raise


@celery_app.task(
    name="app.workers.sync_tasks.sync_education_all",
    bind=True,
    max_retries=3,
)
def sync_education_all(self) -> dict[str, int]:
    """Sync education records from 1C for all employees."""
    log.info("Starting sync_education_all task")
    try:
        result = asyncio.run(_run_sync_education_all())
        log.info("sync_education_all completed", **result)
        return result
    except Exception as exc:
        log.exception("sync_education_all failed", error=str(exc))
        try:
            raise self.retry(exc=exc, countdown=120)
        except MaxRetriesExceededError:
            sentry_sdk.capture_exception(exc)
            raise


@celery_app.task(
    name="app.workers.sync_tasks.send_change_request_email",
    bind=True,
    max_retries=5,
)
def send_change_request_email(self, request_id: str) -> dict[str, Any]:
    """Send email to HR about a newly submitted change request."""
    log.info("Sending change-request email", request_id=request_id)
    try:
        asyncio.run(_send_change_request_email_async(request_id))
        return {"request_id": request_id, "sent": True}
    except Exception as exc:
        log.exception("send_change_request_email failed", request_id=request_id, error=str(exc))
        try:
            raise self.retry(exc=exc, countdown=30)
        except MaxRetriesExceededError:
            sentry_sdk.capture_exception(exc)
            raise
