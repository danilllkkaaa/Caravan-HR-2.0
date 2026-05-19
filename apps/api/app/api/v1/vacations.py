from __future__ import annotations

import uuid
from datetime import date
from typing import Any

from fastapi import APIRouter, Query, Request
from pydantic import BaseModel

from app.api.deps import CurrentEmployee, DBSession, get_client_ip
from app.api.v1._vacation_factory import build_vacation_service
from app.api.v1.vacation_schemas import (
    OverlapCheckOut,
    PaginatedVacationOut,
    VacationBalanceOut,
    VacationRequestOut,
    VacationTypeOut,
)
from app.api.v1.vacation_serializers import VacationRequestSerializer

router = APIRouter(prefix="/vacations", tags=["vacations"])


class CreateVacationRequest(BaseModel):
    vacation_type_id: uuid.UUID
    start_date: date
    end_date: date
    comment: str | None = None
    submit: bool = True


class UpdateVacationRequest(BaseModel):
    start_date: date | None = None
    end_date: date | None = None
    comment: str | None = None
    submit: bool = False


def _with_warnings(
    payload: dict[str, Any], warnings: dict[str, Any]
) -> dict[str, Any]:
    if warnings:
        payload["warnings"] = warnings
    return payload


@router.get("/types", response_model=list[VacationTypeOut])
async def list_vacation_types(
    employee: CurrentEmployee,
    db: DBSession,
) -> list[dict[str, Any]]:
    service = build_vacation_service(db)
    types = await service.list_types()
    return [
        {
            "id": str(t.id),
            "code": t.code,
            "name": t.name,
            "is_paid": t.is_paid,
            "requires_documents": t.requires_documents,
        }
        for t in types
    ]


@router.get("/balance", response_model=VacationBalanceOut)
async def get_vacation_balance(
    employee: CurrentEmployee,
    db: DBSession,
    year: int | None = Query(default=None),
) -> dict[str, Any]:
    if year is None:
        year = date.today().year
    service = build_vacation_service(db)
    balance = await service.get_balance(employee.id, year)
    if balance is None:
        return {"year": year, "total_days": 0.0, "used_days": 0.0, "available_days": 0.0}
    return {
        "year": balance.year,
        "total_days": float(balance.total_days),
        "used_days": float(balance.used_days),
        "available_days": float(balance.available_days),
    }


@router.get("/check-overlap", response_model=OverlapCheckOut)
async def check_overlap(
    employee: CurrentEmployee,
    db: DBSession,
    start_date: date = Query(...),
    end_date: date = Query(...),
    exclude_id: uuid.UUID | None = Query(default=None),
) -> dict[str, bool]:
    service = build_vacation_service(db)
    has_overlap = await service.check_overlap(
        employee.id, start_date, end_date, exclude_id
    )
    return {"has_overlap": has_overlap}


@router.get("", response_model=PaginatedVacationOut)
async def list_vacations(
    employee: CurrentEmployee,
    db: DBSession,
    status: str | None = Query(default=None),
    year: int | None = Query(default=None),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
) -> dict[str, Any]:
    service = build_vacation_service(db)
    requests, total = await service.list_requests(
        employee.id, employee.role, status, offset, limit
    )
    if year is not None:
        requests = [
            r
            for r in requests
            if r.start_date.year == year or r.end_date.year == year
        ]
        total = len(requests)

    serializer = VacationRequestSerializer(db)
    return {
        "items": await serializer.many(requests),
        "total": total,
        "offset": offset,
        "limit": limit,
    }


@router.post("", status_code=201, response_model=VacationRequestOut)
async def create_vacation(
    body: CreateVacationRequest,
    request: Request,
    employee: CurrentEmployee,
    db: DBSession,
) -> dict[str, Any]:
    service = build_vacation_service(db)
    vr, warnings = await service.create_request(
        employee_id=employee.id,
        actor_user_id=employee.user_id,
        vacation_type_id=body.vacation_type_id,
        start_date=body.start_date,
        end_date=body.end_date,
        comment=body.comment,
        submit=body.submit,
        actor_ip=get_client_ip(request),
    )
    serializer = VacationRequestSerializer(db)
    return _with_warnings(await serializer.one(vr), warnings)


@router.get("/{request_id}", response_model=VacationRequestOut)
async def get_vacation(
    request_id: uuid.UUID,
    employee: CurrentEmployee,
    db: DBSession,
) -> dict[str, Any]:
    service = build_vacation_service(db)
    vr = await service.get_request(request_id, employee.id, employee.role)
    serializer = VacationRequestSerializer(db)
    include_employee = employee.role in ("manager", "hr", "admin") and vr.employee_id != employee.id
    return await serializer.one(vr, include_employee=include_employee)


@router.patch("/{request_id}", response_model=VacationRequestOut)
async def update_vacation(
    request_id: uuid.UUID,
    body: UpdateVacationRequest,
    request: Request,
    employee: CurrentEmployee,
    db: DBSession,
) -> dict[str, Any]:
    service = build_vacation_service(db)
    update_data = body.model_dump(exclude_none=True, exclude={"submit"})
    vr, warnings = await service.update_request(
        request_id,
        employee.id,
        employee.role,
        update_data,
        body.submit,
        actor_user_id=employee.user_id,
        actor_ip=get_client_ip(request),
    )
    serializer = VacationRequestSerializer(db)
    return _with_warnings(await serializer.one(vr), warnings)


@router.delete("/{request_id}", status_code=204)
async def cancel_vacation(
    request_id: uuid.UUID,
    request: Request,
    employee: CurrentEmployee,
    db: DBSession,
) -> None:
    service = build_vacation_service(db)
    await service.cancel_request(
        request_id,
        employee.id,
        employee.role,
        actor_user_id=employee.user_id,
        actor_ip=get_client_ip(request),
    )
