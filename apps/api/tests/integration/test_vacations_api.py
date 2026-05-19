from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.security import create_access_token, hash_password
from app.infrastructure.models import (
    Department,
    Employee,
    Position,
    User,
    VacationBalance,
    VacationType,
)


async def _seed_employee(session: AsyncSession, role: str = "employee") -> tuple[User, Employee]:
    suffix = uuid.uuid4().hex[:8]
    dept = Department(
        id=uuid.uuid4(),
        external_id_1c=f"D-{suffix}",
        name="IT",
    )
    pos = Position(id=uuid.uuid4(), external_id_1c=f"POS-{suffix}", name="Developer")
    user = User(
        id=uuid.uuid4(),
        email=f"{role}-{uuid.uuid4().hex[:8]}@test.com",
        password_hash=hash_password("TestPass123!"),
        is_active=True,
    )
    employee = Employee(
        id=uuid.uuid4(),
        user_id=user.id,
        external_id_1c=f"EMP-{uuid.uuid4().hex[:6]}",
        personnel_number="1001",
        first_name="Test",
        last_name="User",
        department_id=dept.id,
        position_id=pos.id,
        role=role,
        hire_date=date(2020, 1, 1),
    )
    session.add_all([dept, pos, user, employee])
    await session.flush()
    return user, employee


@pytest.mark.asyncio
async def test_vacation_flow_create_and_approve(db_engine, test_settings) -> None:
    from app.api.deps import get_db, get_redis_client
    from app.main import app

    session_factory = async_sessionmaker(
        bind=db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )

    async with session_factory() as session:
        manager_user, manager = await _seed_employee(session, role="manager")
        employee_user, employee = await _seed_employee(session, role="employee")
        employee.manager_id = manager.id

        vtype = VacationType(
            id=uuid.uuid4(),
            code="ANNUAL_TEST",
            name="Annual",
            is_paid=True,
            requires_documents=False,
        )
        balance = VacationBalance(
            id=uuid.uuid4(),
            employee_id=employee.id,
            year=2026,
            total_days=Decimal("24"),
            used_days=Decimal("0"),
            sync_source="manual",
        )
        session.add_all([vtype, balance])
        await session.commit()

        employee_token = create_access_token(str(employee_user.id), employee.role)
        manager_token = create_access_token(str(manager_user.id), manager.role)
        type_id = str(vtype.id)

    async def _override_db():
        async with session_factory() as s:
            try:
                yield s
                await s.commit()
            except Exception:
                await s.rollback()
                raise

    from unittest.mock import AsyncMock

    redis = AsyncMock()
    redis.get = AsyncMock(return_value=None)
    redis.setex = AsyncMock(return_value=True)
    redis.ping = AsyncMock(return_value=True)

    app.dependency_overrides[get_db] = _override_db
    app.dependency_overrides[get_redis_client] = lambda: redis

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
    ) as client:
        create_resp = await client.post(
            "/api/v1/vacations",
            json={
                "vacation_type_id": type_id,
                "start_date": "2026-09-01",
                "end_date": "2026-09-05",
                "comment": "Family trip",
                "submit": True,
            },
            headers={"Authorization": f"Bearer {employee_token}"},
        )
        assert create_resp.status_code == 201, create_resp.text
        body = create_resp.json()
        assert body["status"] == "pending"
        request_id = body["id"]

        approve_resp = await client.post(
            f"/api/v1/approvals/vacations/{request_id}/approve",
            json={"comment": "OK"},
            headers={"Authorization": f"Bearer {manager_token}"},
        )
        assert approve_resp.status_code == 200, approve_resp.text
        assert approve_resp.json()["status"] == "approved"

        notif_resp = await client.get(
            "/api/v1/notifications",
            headers={"Authorization": f"Bearer {employee_token}"},
        )
        assert notif_resp.status_code == 200
        assert notif_resp.json()["total"] >= 1

    app.dependency_overrides.clear()
