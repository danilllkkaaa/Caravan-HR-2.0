from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models import RefreshTokenDomain, UserDomain
from app.domain.repositories import AbstractRefreshTokenRepository, AbstractUserRepository
from app.infrastructure.models import RefreshToken, User


def _user_to_domain(user: User) -> UserDomain:
    return UserDomain(
        id=user.id,
        email=user.email,
        password_hash=user.password_hash,
        is_active=user.is_active,
        failed_login_attempts=user.failed_login_attempts,
        locked_until=user.locked_until,
        created_at=user.created_at,
        updated_at=user.updated_at,
    )


def _refresh_token_to_domain(rt: RefreshToken) -> RefreshTokenDomain:
    return RefreshTokenDomain(
        id=rt.id,
        user_id=rt.user_id,
        token_hash=rt.token_hash,
        device_info=rt.device_info,
        expires_at=rt.expires_at,
        revoked_at=rt.revoked_at,
        created_at=rt.created_at,
    )


class UserRepository(AbstractUserRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, user_id: uuid.UUID) -> UserDomain | None:
        result = await self._session.get(User, user_id)
        return _user_to_domain(result) if result else None

    async def get_by_email(self, email: str) -> UserDomain | None:
        stmt = select(User).where(User.email == email.lower())
        result = await self._session.execute(stmt)
        user = result.scalar_one_or_none()
        return _user_to_domain(user) if user else None

    async def create(self, email: str, password_hash: str) -> UserDomain:
        user = User(
            id=uuid.uuid4(),
            email=email.lower(),
            password_hash=password_hash,
            is_active=True,
            failed_login_attempts=0,
        )
        self._session.add(user)
        await self._session.flush()
        await self._session.refresh(user)
        return _user_to_domain(user)

    async def update_failed_attempts(
        self,
        user_id: uuid.UUID,
        attempts: int,
        locked_until: datetime | None,
    ) -> None:
        stmt = (
            update(User)
            .where(User.id == user_id)
            .values(failed_login_attempts=attempts, locked_until=locked_until)
        )
        await self._session.execute(stmt)

    async def reset_failed_attempts(self, user_id: uuid.UUID) -> None:
        stmt = (
            update(User)
            .where(User.id == user_id)
            .values(failed_login_attempts=0, locked_until=None)
        )
        await self._session.execute(stmt)

    async def update_password_hash(self, user_id: uuid.UUID, password_hash: str) -> None:
        stmt = (
            update(User)
            .where(User.id == user_id)
            .values(
                password_hash=password_hash,
                failed_login_attempts=0,
                locked_until=None,
            )
        )
        await self._session.execute(stmt)


class RefreshTokenRepository(AbstractRefreshTokenRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        user_id: uuid.UUID,
        token_hash: str,
        device_info: dict[str, Any],
        expires_at: datetime,
    ) -> RefreshTokenDomain:
        rt = RefreshToken(
            id=uuid.uuid4(),
            user_id=user_id,
            token_hash=token_hash,
            device_info=device_info,
            expires_at=expires_at,
        )
        self._session.add(rt)
        await self._session.flush()
        await self._session.refresh(rt)
        return _refresh_token_to_domain(rt)

    async def get_by_hash(self, token_hash: str) -> RefreshTokenDomain | None:
        stmt = select(RefreshToken).where(RefreshToken.token_hash == token_hash)
        result = await self._session.execute(stmt)
        rt = result.scalar_one_or_none()
        return _refresh_token_to_domain(rt) if rt else None

    async def get_by_id(self, token_id: uuid.UUID) -> RefreshTokenDomain | None:
        result = await self._session.get(RefreshToken, token_id)
        return _refresh_token_to_domain(result) if result else None

    async def revoke(self, token_id: uuid.UUID) -> None:

        stmt = (
            update(RefreshToken)
            .where(RefreshToken.id == token_id)
            .values(revoked_at=datetime.now(UTC))
        )
        await self._session.execute(stmt)

    async def revoke_all_for_user(self, user_id: uuid.UUID) -> None:

        stmt = (
            update(RefreshToken)
            .where(RefreshToken.user_id == user_id, RefreshToken.revoked_at.is_(None))
            .values(revoked_at=datetime.now(UTC))
        )
        await self._session.execute(stmt)

    async def list_active_for_user(self, user_id: uuid.UUID) -> list[RefreshTokenDomain]:

        now = datetime.now(UTC)
        stmt = select(RefreshToken).where(
            RefreshToken.user_id == user_id,
            RefreshToken.revoked_at.is_(None),
            RefreshToken.expires_at > now,
        )
        result = await self._session.execute(stmt)
        return [_refresh_token_to_domain(rt) for rt in result.scalars().all()]
