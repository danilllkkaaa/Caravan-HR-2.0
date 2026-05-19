from __future__ import annotations

import uuid
from datetime import date, timedelta

import structlog

from app.core.config import get_settings
from app.core.exceptions import ConflictError, ForbiddenError, NotFoundError
from app.domain.models import SickLeaveDomain
from app.domain.repositories import AbstractSickLeaveRepository

log = structlog.get_logger(__name__)
settings = get_settings()


class SickLeaveService:
    def __init__(self, sick_leave_repo: AbstractSickLeaveRepository) -> None:
        self._repo = sick_leave_repo

    async def open_sick_leave(
        self,
        employee_id: uuid.UUID,
        start_date: date,
        comment: str | None,
    ) -> SickLeaveDomain:
        existing = await self._repo.get_open_for_employee(employee_id)
        if existing:
            raise ConflictError(message="Employee already has an open sick leave")
        sl = await self._repo.create(
            employee_id,
            {
                "start_date": start_date,
                "end_date": None,
                "open_comment": comment,
                "status": "open",
            },
        )
        log.info("Sick leave opened", sick_leave_id=str(sl.id), employee_id=str(employee_id))
        return sl

    async def get_open(self, employee_id: uuid.UUID) -> SickLeaveDomain | None:
        return await self._repo.get_open_for_employee(employee_id)

    async def close_sick_leave(
        self,
        sick_leave_id: uuid.UUID,
        requester_employee_id: uuid.UUID,
        role: str,
        end_date: date,
        comment: str | None,
    ) -> SickLeaveDomain:
        sl = await self._repo.get_by_id(sick_leave_id)
        if sl is None:
            raise NotFoundError(message="Sick leave not found")
        self._check_write_access(sl, requester_employee_id, role)
        if sl.status != "open":
            raise ConflictError(message="Sick leave is already closed")
        if end_date < sl.start_date:
            raise ConflictError(message="End date cannot be before start date")
        updated = await self._repo.update(
            sick_leave_id,
            {
                "end_date": end_date,
                "close_comment": comment,
                "status": "closed",
                "closed_by": requester_employee_id,
            },
        )
        log.info("Sick leave closed", sick_leave_id=str(sick_leave_id))
        return updated

    async def attach_document_url(
        self,
        sick_leave_id: uuid.UUID,
        requester_employee_id: uuid.UUID,
        role: str,
        document_url: str,
    ) -> SickLeaveDomain:
        sl = await self._repo.get_by_id(sick_leave_id)
        if sl is None:
            raise NotFoundError(message="Sick leave not found")
        self._check_write_access(sl, requester_employee_id, role)
        return await self._repo.update(sick_leave_id, {"document_url": document_url})

    async def generate_upload_url(
        self,
        sick_leave_id: uuid.UUID,
        requester_employee_id: uuid.UUID,
        role: str,
        filename: str,
    ) -> dict[str, str]:
        sl = await self._repo.get_by_id(sick_leave_id)
        if sl is None:
            raise NotFoundError(message="Sick leave not found")
        self._check_write_access(sl, requester_employee_id, role)

        from minio import Minio

        client = Minio(
            settings.minio_endpoint,
            access_key=settings.minio_access_key,
            secret_key=settings.minio_secret_key,
            secure=settings.minio_secure,
        )
        object_name = f"sick-leave/{sick_leave_id}/{filename}"
        url = client.presigned_put_object(
            bucket_name=settings.minio_bucket_sick_leave,
            object_name=object_name,
            expires=timedelta(hours=1),
        )
        public_url = (
            f"{'https' if settings.minio_secure else 'http'}://"
            f"{settings.minio_endpoint}/{settings.minio_bucket_sick_leave}/{object_name}"
        )
        return {"upload_url": url, "object_url": public_url}

    async def list_for_employee(
        self, employee_id: uuid.UUID, offset: int, limit: int
    ) -> tuple[list[SickLeaveDomain], int]:
        return await self._repo.list_for_employee(employee_id, offset, limit)

    async def get_by_id(
        self,
        sick_leave_id: uuid.UUID,
        requester_employee_id: uuid.UUID,
        role: str,
    ) -> SickLeaveDomain:
        sl = await self._repo.get_by_id(sick_leave_id)
        if sl is None:
            raise NotFoundError()
        self._check_read_access(sl, requester_employee_id, role)
        return sl

    def _check_read_access(
        self, sl: SickLeaveDomain, requester_id: uuid.UUID, role: str
    ) -> None:
        if role in ("admin", "hr", "manager"):
            return
        if sl.employee_id != requester_id:
            raise ForbiddenError()

    def _check_write_access(
        self, sl: SickLeaveDomain, requester_id: uuid.UUID, role: str
    ) -> None:
        if role in ("admin", "hr"):
            return
        if sl.employee_id != requester_id:
            raise ForbiddenError()
