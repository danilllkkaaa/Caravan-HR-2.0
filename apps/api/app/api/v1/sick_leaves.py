from __future__ import annotations

import uuid
from datetime import date
from typing import Any

from fastapi import APIRouter, Query
from pydantic import BaseModel

from app.api.deps import CurrentEmployee, DBSession
from app.application.services.sick_leave import SickLeaveService
from app.infrastructure.repositories.sick_leave import SickLeaveRepository

router = APIRouter(prefix="/sick-leaves", tags=["sick-leaves"])


def _get_service(db: DBSession) -> SickLeaveService:
    return SickLeaveService(sick_leave_repo=SickLeaveRepository(db))


class OpenSickLeaveRequest(BaseModel):
    start_date: date
    comment: str | None = None


class CloseSickLeaveRequest(BaseModel):
    end_date: date
    comment: str | None = None


class AttachDocumentRequest(BaseModel):
    document_url: str


def _format_sl(sl: Any) -> dict[str, Any]:
    return {
        "id": str(sl.id),
        "employee_id": str(sl.employee_id),
        "start_date": sl.start_date.isoformat(),
        "end_date": sl.end_date.isoformat() if sl.end_date else None,
        "open_comment": sl.open_comment,
        "close_comment": sl.close_comment,
        "document_url": sl.document_url,
        "status": sl.status,
        "closed_by": str(sl.closed_by) if sl.closed_by else None,
        "created_at": sl.created_at.isoformat(),
        "updated_at": sl.updated_at.isoformat(),
    }


@router.get("")
async def list_sick_leaves(
    employee: CurrentEmployee,
    db: DBSession,
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
) -> dict[str, Any]:
    service = _get_service(db)
    items, total = await service.list_for_employee(employee.id, offset, limit)
    return {
        "items": [_format_sl(sl) for sl in items],
        "total": total,
        "offset": offset,
        "limit": limit,
    }


@router.post("", status_code=201)
async def open_sick_leave(
    body: OpenSickLeaveRequest,
    employee: CurrentEmployee,
    db: DBSession,
) -> dict[str, Any]:
    service = _get_service(db)
    sl = await service.open_sick_leave(employee.id, body.start_date, body.comment)
    return _format_sl(sl)


@router.get("/open")
async def get_open_sick_leave(
    employee: CurrentEmployee,
    db: DBSession,
) -> dict[str, Any] | None:
    service = _get_service(db)
    sl = await service.get_open(employee.id)
    return _format_sl(sl) if sl else None


@router.get("/{sick_leave_id}")
async def get_sick_leave(
    sick_leave_id: uuid.UUID,
    employee: CurrentEmployee,
    db: DBSession,
) -> dict[str, Any]:
    service = _get_service(db)
    sl = await service.get_by_id(sick_leave_id, employee.id, employee.role)
    return _format_sl(sl)


@router.post("/{sick_leave_id}/close")
async def close_sick_leave(
    sick_leave_id: uuid.UUID,
    body: CloseSickLeaveRequest,
    employee: CurrentEmployee,
    db: DBSession,
) -> dict[str, Any]:
    service = _get_service(db)
    sl = await service.close_sick_leave(
        sick_leave_id, employee.id, employee.role, body.end_date, body.comment
    )
    return _format_sl(sl)


@router.post("/{sick_leave_id}/document")
async def attach_document(
    sick_leave_id: uuid.UUID,
    body: AttachDocumentRequest,
    employee: CurrentEmployee,
    db: DBSession,
) -> dict[str, Any]:
    service = _get_service(db)
    sl = await service.attach_document_url(
        sick_leave_id, employee.id, employee.role, body.document_url
    )
    return _format_sl(sl)


@router.post("/upload-url")
async def get_upload_url(
    sick_leave_id: uuid.UUID,
    filename: str,
    employee: CurrentEmployee,
    db: DBSession,
) -> dict[str, str]:
    service = _get_service(db)
    return await service.generate_upload_url(sick_leave_id, employee.id, employee.role, filename)
