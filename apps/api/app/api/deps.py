from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from typing import Annotated

import redis.asyncio as aioredis
from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ForbiddenError, NotFoundError, UnauthorizedError
from app.core.security import decode_access_token
from app.domain.models import EmployeeDomain, UserDomain
from app.infrastructure.database import get_db_session, get_redis
from app.infrastructure.repositories.employee import EmployeeRepository
from app.infrastructure.repositories.user import UserRepository

bearer_scheme = HTTPBearer(auto_error=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async for session in get_db_session():
        yield session


async def get_redis_client() -> aioredis.Redis:
    return get_redis()


DBSession = Annotated[AsyncSession, Depends(get_db)]
RedisClient = Annotated[aioredis.Redis, Depends(get_redis_client)]


async def get_current_user(
    request: Request,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)] = None,
    db: AsyncSession = Depends(get_db),
) -> UserDomain:
    token: str | None = None
    if credentials:
        token = credentials.credentials
    else:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header[7:]

    if not token:
        raise UnauthorizedError(message="No authentication token provided")

    try:
        payload = decode_access_token(token)
    except JWTError as e:
        raise UnauthorizedError(message=f"Invalid token: {e}") from e

    token_type = payload.get("type")
    if token_type != "access":
        raise UnauthorizedError(message="Invalid token type")

    user_id_str: str | None = payload.get("sub")
    if not user_id_str:
        raise UnauthorizedError(message="Token missing subject")

    try:
        user_id = uuid.UUID(user_id_str)
    except ValueError as exc:
        raise UnauthorizedError(message="Invalid token subject") from exc

    user_repo = UserRepository(db)
    user = await user_repo.get_by_id(user_id)
    if user is None:
        raise UnauthorizedError(message="User not found")
    if not user.is_active:
        raise UnauthorizedError(message="Account is disabled")

    # Store role from token in request state for quick access
    request.state.token_role = payload.get("role", "employee")
    return user


CurrentUser = Annotated[UserDomain, Depends(get_current_user)]


async def get_current_employee(
    request: Request,
    user: CurrentUser,
    db: DBSession,
) -> EmployeeDomain:
    employee_repo = EmployeeRepository(db)
    employee = await employee_repo.get_by_user_id(user.id)
    if employee is None:
        raise NotFoundError(message="Employee profile not found for this user")
    return employee


CurrentEmployee = Annotated[EmployeeDomain, Depends(get_current_employee)]


def require_roles(*roles: str):
    async def _check(
        request: Request,
        employee: EmployeeDomain = Depends(get_current_employee),
    ) -> EmployeeDomain:
        if employee.role not in roles:
            raise ForbiddenError(
                message=f"Required roles: {roles}. Your role: {employee.role}"
            )
        return employee

    return _check


def get_client_ip(request: Request) -> str:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host
    return "unknown"


def get_device_info(request: Request) -> dict:
    return {
        "user_agent": request.headers.get("User-Agent", ""),
        "ip": get_client_ip(request),
    }
