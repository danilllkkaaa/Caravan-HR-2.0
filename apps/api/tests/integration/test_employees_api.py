from __future__ import annotations

import uuid
from datetime import date
from unittest.mock import AsyncMock

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.security import create_access_token, hash_password
from app.infrastructure.models import Department, Employee, Position, User


async def _seed_employee(
    session: AsyncSession,
    *,
    role: str = "employee",
    department: Department | None = None,
    position: Position | None = None,
    manager_id: uuid.UUID | None = None,
) -> tuple[User, Employee, Department, Position]:
    suffix = uuid.uuid4().hex[:8]
    department = department or Department(
        id=uuid.uuid4(),
        external_id_1c=f"D-{suffix}",
        name=f"Department {suffix}",
    )
    position = position or Position(
        id=uuid.uuid4(),
        external_id_1c=f"P-{suffix}",
        name=f"Position {suffix}",
    )
    user = User(
        id=uuid.uuid4(),
        email=f"{role}-{suffix}@test.com",
        password_hash=hash_password("TestPass123!"),
        is_active=True,
    )
    employee = Employee(
        id=uuid.uuid4(),
        user_id=user.id,
        external_id_1c=f"E-{suffix}",
        personnel_number=suffix,
        first_name="Test",
        last_name=role.title(),
        department_id=department.id,
        position_id=position.id,
        manager_id=manager_id,
        role=role,
        hire_date=date(2020, 1, 1),
    )
    session.add_all([department, position, user, employee])
    await session.flush()
    return user, employee, department, position


@pytest.mark.asyncio
async def test_employee_profile_direct_reports_and_directories(db_engine) -> None:
    from app.api.deps import get_db, get_redis_client
    from app.main import app

    session_factory = async_sessionmaker(
        bind=db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )

    async with session_factory() as session:
        manager_user, manager, department, position = await _seed_employee(
            session, role="manager"
        )
        employee_user, employee, _, _ = await _seed_employee(
            session,
            department=department,
            position=position,
            manager_id=manager.id,
        )
        await session.commit()

        manager_token = create_access_token(str(manager_user.id), manager.role)
        employee_token = create_access_token(str(employee_user.id), employee.role)
        department_id = str(department.id)
        position_id = str(position.id)

    async def _override_db():
        async with session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

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
        departments_resp = await client.get(
            "/api/v1/departments",
            headers={"Authorization": f"Bearer {employee_token}"},
        )
        assert departments_resp.status_code == 200, departments_resp.text
        assert any(item["id"] == department_id for item in departments_resp.json())

        positions_resp = await client.get(
            "/api/v1/positions",
            headers={"Authorization": f"Bearer {employee_token}"},
        )
        assert positions_resp.status_code == 200, positions_resp.text
        assert any(item["id"] == position_id for item in positions_resp.json())

        direct_reports_resp = await client.get(
            "/api/v1/employees/direct-reports",
            headers={"Authorization": f"Bearer {manager_token}"},
        )
        assert direct_reports_resp.status_code == 200, direct_reports_resp.text
        assert direct_reports_resp.json()[0]["manager_id"] == str(manager.id)

        update_resp = await client.patch(
            "/api/v1/employees/me",
            json={"phone": "+7 777 000 00 00"},
            headers={"Authorization": f"Bearer {employee_token}"},
        )
        assert update_resp.status_code == 200, update_resp.text
        assert update_resp.json()["phone"] == "+7 777 000 00 00"

    app.dependency_overrides.clear()
