from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

import structlog

from app.core.config import get_settings
from app.core.exceptions import (
    AccountLockedError,
    InvalidCredentialsError,
    NotFoundError,
    TokenExpiredError,
    TokenRevokedError,
)
from app.core.security import (
    create_access_token,
    generate_refresh_token,
    hash_password,
    hash_refresh_token,
    refresh_token_expires_at,
    verify_password,
)
from app.domain.models import RefreshTokenDomain, UserDomain
from app.domain.repositories import AbstractRefreshTokenRepository, AbstractUserRepository

settings = get_settings()
log = structlog.get_logger(__name__)


class AuthService:
    def __init__(
        self,
        user_repo: AbstractUserRepository,
        refresh_token_repo: AbstractRefreshTokenRepository,
    ) -> None:
        self._user_repo = user_repo
        self._rt_repo = refresh_token_repo

    async def login(
        self,
        email: str,
        password: str,
        device_info: dict[str, Any],
    ) -> dict[str, Any]:
        user = await self._user_repo.get_by_email(email)

        if user is None:
            log.warning("Login attempt for unknown email", email=email)
            raise InvalidCredentialsError()

        if not user.is_active:
            raise InvalidCredentialsError(message="Account is disabled")

        # Check if account is locked
        if user.locked_until and user.locked_until > datetime.now(UTC):
            raise AccountLockedError(
                details={"locked_until": user.locked_until.isoformat()}
            )

        if not verify_password(password, user.password_hash):
            new_attempts = user.failed_login_attempts + 1
            locked_until: datetime | None = None
            if new_attempts >= settings.max_failed_login_attempts:
                from datetime import timedelta

                locked_until = datetime.now(UTC) + timedelta(
                    minutes=settings.account_lock_minutes
                )
                log.warning(
                    "Account locked after failed attempts",
                    user_id=str(user.id),
                    attempts=new_attempts,
                )
            await self._user_repo.update_failed_attempts(user.id, new_attempts, locked_until)
            raise InvalidCredentialsError()

        # Successful login - reset failed attempts
        await self._user_repo.reset_failed_attempts(user.id)

        return await self._create_token_pair(user, device_info)

    async def refresh(
        self,
        raw_token: str,
        device_info: dict[str, Any],
    ) -> dict[str, Any]:
        token_hash = hash_refresh_token(raw_token)
        rt = await self._rt_repo.get_by_hash(token_hash)

        if rt is None:
            raise TokenRevokedError()

        if rt.revoked_at is not None:
            log.warning(
                "Revoked refresh token rejected",
                user_id=str(rt.user_id),
            )
            raise TokenRevokedError()

        if rt.expires_at < datetime.now(UTC):
            await self._rt_repo.revoke(rt.id)
            raise TokenExpiredError()

        user = await self._user_repo.get_by_id(rt.user_id)
        if user is None or not user.is_active:
            await self._rt_repo.revoke(rt.id)
            raise InvalidCredentialsError()

        # Revoke old token
        await self._rt_repo.revoke(rt.id)

        # Issue new pair
        return await self._create_token_pair(user, device_info)

    async def logout(self, raw_token: str) -> None:
        token_hash = hash_refresh_token(raw_token)
        rt = await self._rt_repo.get_by_hash(token_hash)
        if rt and rt.revoked_at is None:
            await self._rt_repo.revoke(rt.id)

    async def logout_all(self, user_id: uuid.UUID) -> None:
        await self._rt_repo.revoke_all_for_user(user_id)

    async def get_sessions(self, user_id: uuid.UUID) -> list[RefreshTokenDomain]:
        return await self._rt_repo.list_active_for_user(user_id)

    async def revoke_session(self, user_id: uuid.UUID, session_id: uuid.UUID) -> None:
        rt = await self._rt_repo.get_by_id(session_id)
        if rt is None:
            raise NotFoundError(message="Session not found")
        if rt.user_id != user_id:
            raise NotFoundError(message="Session not found")
        await self._rt_repo.revoke(session_id)

    async def change_password(
        self, user_id: uuid.UUID, current_password: str, new_password: str
    ) -> None:
        user = await self._user_repo.get_by_id(user_id)
        if user is None or not user.is_active:
            raise InvalidCredentialsError()
        if not verify_password(current_password, user.password_hash):
            raise InvalidCredentialsError(message="Current password is incorrect")
        await self._user_repo.update_password_hash(user.id, hash_password(new_password))
        await self._rt_repo.revoke_all_for_user(user.id)

    async def _create_token_pair(
        self, user: UserDomain, device_info: dict[str, Any]
    ) -> dict[str, Any]:
        employee_role = "employee"

        raw_refresh = generate_refresh_token()
        token_hash = hash_refresh_token(raw_refresh)
        expires_at = refresh_token_expires_at()

        await self._rt_repo.create(
            user_id=user.id,
            token_hash=token_hash,
            device_info=device_info,
            expires_at=expires_at,
        )

        access_token = create_access_token(
            subject=str(user.id),
            role=employee_role,
        )

        log.info("Token pair created", user_id=str(user.id))

        return {
            "access_token": access_token,
            "refresh_token": raw_refresh,
            "refresh_expires_at": expires_at,
            "token_type": "bearer",
        }


class AuthServiceWithRole(AuthService):
    """AuthService that fetches employee role for token creation."""

    def __init__(
        self,
        user_repo: AbstractUserRepository,
        refresh_token_repo: AbstractRefreshTokenRepository,
        employee_repo: Any,
    ) -> None:
        super().__init__(user_repo, refresh_token_repo)
        self._employee_repo = employee_repo

    async def _create_token_pair(
        self, user: UserDomain, device_info: dict[str, Any]
    ) -> dict[str, Any]:
        employee = await self._employee_repo.get_by_user_id(user.id)
        role = employee.role if employee else "employee"

        raw_refresh = generate_refresh_token()
        token_hash = hash_refresh_token(raw_refresh)
        expires_at = refresh_token_expires_at()

        await self._rt_repo.create(
            user_id=user.id,
            token_hash=token_hash,
            device_info=device_info,
            expires_at=expires_at,
        )

        access_token = create_access_token(
            subject=str(user.id),
            role=role,
        )

        log.info("Token pair created", user_id=str(user.id), role=role)

        return {
            "access_token": access_token,
            "refresh_token": raw_refresh,
            "refresh_expires_at": expires_at,
            "token_type": "bearer",
        }
