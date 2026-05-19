from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock

import pytest

from app.application.services.auth import AuthServiceWithRole
from app.core.exceptions import (
    AccountLockedError,
    InvalidCredentialsError,
    TokenExpiredError,
    TokenRevokedError,
)
from app.core.security import generate_refresh_token, hash_password, hash_refresh_token
from app.domain.models import EmployeeDomain, RefreshTokenDomain, UserDomain


def make_user(**kwargs) -> UserDomain:
    defaults = dict(
        id=uuid.uuid4(),
        email="test@example.com",
        password_hash=hash_password("ValidPass123!"),
        is_active=True,
        failed_login_attempts=0,
        locked_until=None,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    defaults.update(kwargs)
    return UserDomain(**defaults)


def make_refresh_token(user_id: uuid.UUID, **kwargs) -> tuple[str, RefreshTokenDomain]:
    raw = generate_refresh_token()
    token_hash = hash_refresh_token(raw)
    defaults = dict(
        id=uuid.uuid4(),
        user_id=user_id,
        token_hash=token_hash,
        device_info={"user_agent": "Test", "ip": "127.0.0.1"},
        expires_at=datetime.now(UTC) + timedelta(days=30),
        revoked_at=None,
        created_at=datetime.now(UTC),
    )
    defaults.update(kwargs)
    return raw, RefreshTokenDomain(**defaults)


def make_employee(user_id: uuid.UUID, role: str = "employee") -> EmployeeDomain:
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


@pytest.fixture
def user_repo():
    return AsyncMock()


@pytest.fixture
def rt_repo():
    return AsyncMock()


@pytest.fixture
def employee_repo():
    return AsyncMock()


@pytest.fixture
def auth_service(user_repo, rt_repo, employee_repo) -> AuthServiceWithRole:
    return AuthServiceWithRole(
        user_repo=user_repo,
        refresh_token_repo=rt_repo,
        employee_repo=employee_repo,
    )


class TestLogin:
    async def test_login_success(self, auth_service, user_repo, rt_repo, employee_repo):
        user = make_user()
        employee = make_employee(user.id)
        user_repo.get_by_email.return_value = user
        user_repo.reset_failed_attempts.return_value = None
        rt_repo.create.return_value = make_refresh_token(user.id)[1]
        employee_repo.get_by_user_id.return_value = employee

        result = await auth_service.login(
            "test@example.com", "ValidPass123!", {"user_agent": "Test", "ip": "127.0.0.1"}
        )

        assert "access_token" in result
        assert "refresh_token" in result
        assert "refresh_expires_at" in result
        assert result["token_type"] == "bearer"
        user_repo.reset_failed_attempts.assert_awaited_once()

    async def test_login_unknown_email(self, auth_service, user_repo):
        user_repo.get_by_email.return_value = None
        with pytest.raises(InvalidCredentialsError):
            await auth_service.login("nobody@example.com", "pass", {})

    async def test_login_wrong_password(self, auth_service, user_repo, rt_repo):
        user = make_user()
        user_repo.get_by_email.return_value = user
        user_repo.update_failed_attempts.return_value = None

        with pytest.raises(InvalidCredentialsError):
            await auth_service.login("test@example.com", "WrongPass!", {})

        user_repo.update_failed_attempts.assert_awaited_once()

    async def test_login_locked_account(self, auth_service, user_repo):
        user = make_user(
            locked_until=datetime.now(UTC) + timedelta(minutes=10)
        )
        user_repo.get_by_email.return_value = user

        with pytest.raises(AccountLockedError):
            await auth_service.login("test@example.com", "ValidPass123!", {})

    async def test_login_inactive_account(self, auth_service, user_repo):
        user = make_user(is_active=False)
        user_repo.get_by_email.return_value = user

        with pytest.raises(InvalidCredentialsError):
            await auth_service.login("test@example.com", "ValidPass123!", {})

    async def test_login_increments_failed_attempts(self, auth_service, user_repo):
        user = make_user(failed_login_attempts=2)
        user_repo.get_by_email.return_value = user
        user_repo.update_failed_attempts.return_value = None

        with pytest.raises(InvalidCredentialsError):
            await auth_service.login("test@example.com", "WrongPass!", {})

        user_repo.update_failed_attempts.assert_awaited_once_with(user.id, 3, None)

    async def test_login_locks_after_max_attempts(self, auth_service, user_repo):
        user = make_user(failed_login_attempts=4)  # 5th attempt will lock
        user_repo.get_by_email.return_value = user
        user_repo.update_failed_attempts.return_value = None

        with pytest.raises(InvalidCredentialsError):
            await auth_service.login("test@example.com", "WrongPass!", {})

        call_args = user_repo.update_failed_attempts.call_args
        assert call_args.args[1] == 5  # attempts
        assert call_args.args[2] is not None  # locked_until set


class TestRefresh:
    async def test_refresh_success(self, auth_service, user_repo, rt_repo, employee_repo):
        user = make_user()
        raw_token, rt = make_refresh_token(user.id)
        employee = make_employee(user.id)

        rt_repo.get_by_hash.return_value = rt
        user_repo.get_by_id.return_value = user
        rt_repo.revoke.return_value = None
        rt_repo.create.return_value = make_refresh_token(user.id)[1]
        employee_repo.get_by_user_id.return_value = employee

        result = await auth_service.refresh(raw_token, {})

        assert "access_token" in result
        rt_repo.revoke.assert_awaited_once_with(rt.id)

    async def test_refresh_revoked_token_does_not_revoke_all_sessions(
        self, auth_service, user_repo, rt_repo
    ):
        user = make_user()
        raw_token, rt = make_refresh_token(
            user.id,
            revoked_at=datetime.now(UTC),
        )

        rt_repo.get_by_hash.return_value = rt

        with pytest.raises(TokenRevokedError):
            await auth_service.refresh(raw_token, {})

        rt_repo.revoke_all_for_user.assert_not_awaited()

    async def test_refresh_expired_token(self, auth_service, rt_repo):
        user = make_user()
        raw_token, rt = make_refresh_token(
            user.id,
            expires_at=datetime.now(UTC) - timedelta(hours=1),
        )

        rt_repo.get_by_hash.return_value = rt
        rt_repo.revoke.return_value = None

        with pytest.raises(TokenExpiredError):
            await auth_service.refresh(raw_token, {})

    async def test_refresh_nonexistent_token(self, auth_service, rt_repo):
        rt_repo.get_by_hash.return_value = None

        with pytest.raises(TokenRevokedError):
            await auth_service.refresh("nonexistent-token", {})


class TestLogout:
    async def test_logout_revokes_token(self, auth_service, rt_repo):
        user = make_user()
        raw_token, rt = make_refresh_token(user.id)
        rt_repo.get_by_hash.return_value = rt
        rt_repo.revoke.return_value = None

        await auth_service.logout(raw_token)

        rt_repo.revoke.assert_awaited_once_with(rt.id)

    async def test_logout_nonexistent_token_is_noop(self, auth_service, rt_repo):
        rt_repo.get_by_hash.return_value = None

        await auth_service.logout("bad-token")
        rt_repo.revoke.assert_not_awaited()

    async def test_logout_all(self, auth_service, rt_repo):
        user_id = uuid.uuid4()
        rt_repo.revoke_all_for_user.return_value = None

        await auth_service.logout_all(user_id)

        rt_repo.revoke_all_for_user.assert_awaited_once_with(user_id)


class TestChangePassword:
    async def test_change_password_updates_hash_and_revokes_sessions(
        self, auth_service, user_repo, rt_repo
    ):
        user = make_user()
        user_repo.get_by_id.return_value = user
        user_repo.update_password_hash.return_value = None
        rt_repo.revoke_all_for_user.return_value = None

        await auth_service.change_password(user.id, "ValidPass123!", "NewValidPass123!")

        user_repo.update_password_hash.assert_awaited_once()
        called_user_id, new_hash = user_repo.update_password_hash.call_args.args
        assert called_user_id == user.id
        assert new_hash != user.password_hash
        rt_repo.revoke_all_for_user.assert_awaited_once_with(user.id)

    async def test_change_password_rejects_wrong_current_password(
        self, auth_service, user_repo
    ):
        user = make_user()
        user_repo.get_by_id.return_value = user

        with pytest.raises(InvalidCredentialsError):
            await auth_service.change_password(user.id, "WrongPass!", "NewValidPass123!")
