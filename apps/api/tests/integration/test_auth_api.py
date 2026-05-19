from __future__ import annotations

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient

from app.core.security import (
    generate_refresh_token,
    hash_password,
    hash_refresh_token,
    refresh_token_expires_at,
)
from app.domain.models import EmployeeDomain, RefreshTokenDomain, UserDomain


def _make_user(
    email: str = "test@example.com",
    password: str = "TestPass123!",
    is_active: bool = True,
    failed_attempts: int = 0,
    locked_until=None,
) -> UserDomain:

    return UserDomain(
        id=uuid.uuid4(),
        email=email,
        password_hash=hash_password(password),
        is_active=is_active,
        failed_login_attempts=failed_attempts,
        locked_until=locked_until,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


def _make_employee(user_id: uuid.UUID, role: str = "employee") -> EmployeeDomain:
    from datetime import date

    return EmployeeDomain(
        id=uuid.uuid4(),
        user_id=user_id,
        external_id_1c="EMP-001",
        personnel_number="P001",
        first_name="Ivan",
        last_name="Petrov",
        middle_name="",
        birth_date=None,
        phone="",
        department_id=uuid.uuid4(),
        position_id=uuid.uuid4(),
        manager_id=None,
        role=role,
        hire_date=date(2020, 1, 1),
        work_location_id=None,
        avatar_url=None,
        sync_hash="abc",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


def _make_refresh_token(user_id: uuid.UUID) -> tuple[str, RefreshTokenDomain]:
    raw = generate_refresh_token()
    return raw, RefreshTokenDomain(
        id=uuid.uuid4(),
        user_id=user_id,
        token_hash=hash_refresh_token(raw),
        device_info={"user_agent": "TestClient", "ip": "127.0.0.1"},
        expires_at=refresh_token_expires_at(),
        revoked_at=None,
        created_at=datetime.now(UTC),
    )


@pytest.fixture
def mock_auth_repos():
    """Returns (user_repo_mock, rt_repo_mock, employee_repo_mock)."""
    user_repo = AsyncMock()
    rt_repo = AsyncMock()
    employee_repo = AsyncMock()
    return user_repo, rt_repo, employee_repo


@pytest.fixture
def setup_login_mocks(mock_auth_repos):
    user_repo, rt_repo, employee_repo = mock_auth_repos
    user = _make_user()
    employee = _make_employee(user.id)
    raw_token, rt = _make_refresh_token(user.id)

    user_repo.get_by_email.return_value = user
    user_repo.reset_failed_attempts.return_value = None
    rt_repo.create.return_value = rt
    employee_repo.get_by_user_id.return_value = employee

    return user, employee, raw_token, rt, user_repo, rt_repo, employee_repo


class TestLoginEndpoint:
    async def test_login_success(self, async_client: AsyncClient, setup_login_mocks):
        user, employee, raw_token, rt, user_repo, rt_repo, employee_repo = setup_login_mocks

        with (
            patch("app.api.v1.auth.UserRepository", return_value=user_repo),
            patch("app.api.v1.auth.RefreshTokenRepository", return_value=rt_repo),
            patch("app.api.v1.auth.EmployeeRepository", return_value=employee_repo),
        ):
            response = await async_client.post(
                "/api/v1/auth/login",
                json={"email": "test@example.com", "password": "TestPass123!"},
            )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert "Set-Cookie" in response.headers
        cookie = response.headers["Set-Cookie"]
        assert "Path=/api/v1/auth" in cookie
        assert "HttpOnly" in cookie
        assert "SameSite=lax" in cookie
        assert "Secure" not in cookie

    async def test_login_invalid_credentials(self, async_client: AsyncClient, mock_auth_repos):
        user_repo, rt_repo, employee_repo = mock_auth_repos
        user = _make_user()
        user_repo.get_by_email.return_value = user
        user_repo.update_failed_attempts.return_value = None

        with (
            patch("app.api.v1.auth.UserRepository", return_value=user_repo),
            patch("app.api.v1.auth.RefreshTokenRepository", return_value=rt_repo),
            patch("app.api.v1.auth.EmployeeRepository", return_value=employee_repo),
        ):
            response = await async_client.post(
                "/api/v1/auth/login",
                json={"email": "test@example.com", "password": "WrongPass!"},
            )

        assert response.status_code == 401
        assert response.json()["error"]["code"] == "INVALID_CREDENTIALS"

    async def test_login_unknown_email(self, async_client: AsyncClient, mock_auth_repos):
        user_repo, rt_repo, employee_repo = mock_auth_repos
        user_repo.get_by_email.return_value = None

        with (
            patch("app.api.v1.auth.UserRepository", return_value=user_repo),
            patch("app.api.v1.auth.RefreshTokenRepository", return_value=rt_repo),
            patch("app.api.v1.auth.EmployeeRepository", return_value=employee_repo),
        ):
            response = await async_client.post(
                "/api/v1/auth/login",
                json={"email": "nobody@example.com", "password": "AnyPass!"},
            )

        assert response.status_code == 401

    async def test_login_locked_account(self, async_client: AsyncClient, mock_auth_repos):
        from datetime import timedelta

        user_repo, rt_repo, employee_repo = mock_auth_repos
        user = _make_user(
            locked_until=datetime.now(UTC) + timedelta(minutes=10)
        )
        user_repo.get_by_email.return_value = user

        with (
            patch("app.api.v1.auth.UserRepository", return_value=user_repo),
            patch("app.api.v1.auth.RefreshTokenRepository", return_value=rt_repo),
            patch("app.api.v1.auth.EmployeeRepository", return_value=employee_repo),
        ):
            response = await async_client.post(
                "/api/v1/auth/login",
                json={"email": "test@example.com", "password": "TestPass123!"},
            )

        assert response.status_code == 423
        assert response.json()["error"]["code"] == "ACCOUNT_LOCKED"

    async def test_login_validation_error_missing_fields(self, async_client: AsyncClient):
        response = await async_client.post("/api/v1/auth/login", json={})
        assert response.status_code == 422

    async def test_login_inactive_user(self, async_client: AsyncClient, mock_auth_repos):
        user_repo, rt_repo, employee_repo = mock_auth_repos
        user = _make_user(is_active=False)
        user_repo.get_by_email.return_value = user

        with (
            patch("app.api.v1.auth.UserRepository", return_value=user_repo),
            patch("app.api.v1.auth.RefreshTokenRepository", return_value=rt_repo),
            patch("app.api.v1.auth.EmployeeRepository", return_value=employee_repo),
        ):
            response = await async_client.post(
                "/api/v1/auth/login",
                json={"email": "test@example.com", "password": "TestPass123!"},
            )

        assert response.status_code == 401


class TestRefreshEndpoint:
    async def test_refresh_success(self, async_client: AsyncClient, mock_auth_repos):
        user_repo, rt_repo, employee_repo = mock_auth_repos
        user = _make_user()
        employee = _make_employee(user.id)
        raw_old, rt_old = _make_refresh_token(user.id)
        raw_new, rt_new = _make_refresh_token(user.id)

        rt_repo.get_by_hash.return_value = rt_old
        user_repo.get_by_id.return_value = user
        rt_repo.revoke.return_value = None
        rt_repo.create.return_value = rt_new
        employee_repo.get_by_user_id.return_value = employee

        with (
            patch("app.api.v1.auth.UserRepository", return_value=user_repo),
            patch("app.api.v1.auth.RefreshTokenRepository", return_value=rt_repo),
            patch("app.api.v1.auth.EmployeeRepository", return_value=employee_repo),
        ):
            response = await async_client.post(
                "/api/v1/auth/refresh",
                headers={"Authorization-Refresh": raw_old},
            )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data

    async def test_refresh_no_token(self, async_client: AsyncClient):
        response = await async_client.post("/api/v1/auth/refresh")
        assert response.status_code == 401

    async def test_refresh_revoked_token(self, async_client: AsyncClient, mock_auth_repos):
        user_repo, rt_repo, employee_repo = mock_auth_repos
        user = _make_user()
        raw_old, rt_old = _make_refresh_token(user.id)
        rt_revoked = RefreshTokenDomain(
            **{**rt_old.__dict__, "revoked_at": datetime.now(UTC)}
        )

        rt_repo.get_by_hash.return_value = rt_revoked
        rt_repo.revoke_all_for_user.return_value = None

        with (
            patch("app.api.v1.auth.UserRepository", return_value=user_repo),
            patch("app.api.v1.auth.RefreshTokenRepository", return_value=rt_repo),
            patch("app.api.v1.auth.EmployeeRepository", return_value=employee_repo),
        ):
            response = await async_client.post(
                "/api/v1/auth/refresh",
                headers={"Authorization-Refresh": raw_old},
            )

        assert response.status_code == 401
        assert response.json()["error"]["code"] == "TOKEN_REVOKED"
        rt_repo.revoke_all_for_user.assert_not_awaited()


class TestLogoutEndpoint:
    async def test_logout_success(self, async_client: AsyncClient, mock_auth_repos):
        user_repo, rt_repo, employee_repo = mock_auth_repos
        user = _make_user()
        raw, rt = _make_refresh_token(user.id)

        rt_repo.get_by_hash.return_value = rt
        rt_repo.revoke.return_value = None

        with (
            patch("app.api.v1.auth.UserRepository", return_value=user_repo),
            patch("app.api.v1.auth.RefreshTokenRepository", return_value=rt_repo),
            patch("app.api.v1.auth.EmployeeRepository", return_value=employee_repo),
        ):
            response = await async_client.post(
                "/api/v1/auth/logout",
                headers={"Authorization-Refresh": raw},
            )

        assert response.status_code == 204


class TestHealthEndpoints:
    async def test_health(self, async_client: AsyncClient):
        response = await async_client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"

    async def test_versioned_health_alias(self, async_client: AsyncClient):
        response = await async_client.get("/api/v1/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"
