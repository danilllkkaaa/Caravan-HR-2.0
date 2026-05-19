from __future__ import annotations

import uuid
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query, Request
from pydantic import BaseModel, Field

from app.api.deps import DBSession, get_client_ip, require_roles
from app.api.v1._vacation_factory import build_vacation_service
from app.api.v1.vacation_schemas import PaginatedVacationOut, VacationRequestOut
from app.api.v1.vacation_serializers import VacationRequestSerializer
from app.domain.models import EmployeeDomain

router = APIRouter(prefix="/approvals", tags=["approvals"])

ManagerOrAbove = Annotated[EmployeeDomain, Depends(require_roles("manager", "hr", "admin"))]


class ApproveRequest(BaseModel):
    comment: str | None = None


class RejectRequest(BaseModel):
    comment: str = Field(..., min_length=1)


@router.get("/vacations", response_model=PaginatedVacationOut)
async def list_pending_approvals(
    employee: ManagerOrAbove,
    db: DBSession,
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
) -> dict[str, Any]:
    service = build_vacation_service(db)
    requests, total = await service.list_pending_approvals(employee, offset, limit)
    serializer = VacationRequestSerializer(db)
    return {
        "items": await serializer.many(requests, include_employee=True),
        "total": total,
        "offset": offset,
        "limit": limit,
    }


@router.post("/vacations/{request_id}/approve", response_model=VacationRequestOut)
async def approve_vacation(
    request_id: uuid.UUID,
    body: ApproveRequest,
    request: Request,
    employee: ManagerOrAbove,
    db: DBSession,
) -> dict[str, Any]:
    service = build_vacation_service(db)
    vr = await service.approve_request(
        request_id, employee, body.comment, actor_ip=get_client_ip(request)
    )
    serializer = VacationRequestSerializer(db)
    return await serializer.one(vr, include_employee=True)


@router.post("/vacations/{request_id}/reject", response_model=VacationRequestOut)
async def reject_vacation(
    request_id: uuid.UUID,
    body: RejectRequest,
    request: Request,
    employee: ManagerOrAbove,
    db: DBSession,
) -> dict[str, Any]:
    service = build_vacation_service(db)
    vr = await service.reject_request(
        request_id, employee, body.comment, actor_ip=get_client_ip(request)
    )
    serializer = VacationRequestSerializer(db)
    return await serializer.one(vr, include_employee=True)
