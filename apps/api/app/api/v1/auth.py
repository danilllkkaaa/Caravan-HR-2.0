from __future__ import annotations

import uuid
from datetime import datetime
from typing import Annotated, Any

from fastapi import APIRouter, Cookie, Request, Response
from pydantic import BaseModel, EmailStr, Field, field_validator

from app.api.deps import (
    CurrentEmployee,
    CurrentUser,
    DBSession,
    get_device_info,
)
from app.application.services.auth import AuthServiceWithRole
from app.core.config import get_settings
from app.infrastructure.repositories.employee import EmployeeRepository
from app.infrastructure.repositories.user import RefreshTokenRepository, UserRepository

router = APIRouter(prefix="/auth", tags=["auth"])
settings = get_settings()


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=256)

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, value: Any) -> Any:
        if isinstance(value, str):
            return value.strip().lower()
        return value


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(min_length=1, max_length=256)
    new_password: str = Field(min_length=8, max_length=128)

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, value: str) -> str:
        if not any(char.islower() for char in value):
            raise ValueError("Password must contain a lowercase letter")
        if not any(char.isupper() for char in value):
            raise ValueError("Password must contain an uppercase letter")
        if not any(char.isdigit() for char in value):
            raise ValueError("Password must contain a digit")
        return value


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    refresh_expires_at: datetime
    refresh_token: str  # Also returned in body for mobile


class SessionResponse(BaseModel):
    id: uuid.UUID
    device_info: dict[str, Any]
    created_at: datetime
    expires_at: datetime


def _get_auth_service(db: DBSession) -> AuthServiceWithRole:
    return AuthServiceWithRole(
        user_repo=UserRepository(db),
        refresh_token_repo=RefreshTokenRepository(db),
        employee_repo=EmployeeRepository(db),
    )


def _extract_refresh_token(
    request: Request,
    refresh_token_cookie: Annotated[str | None, Cookie(alias="refresh_token")] = None,
) -> str | None:
    if refresh_token_cookie:
        return refresh_token_cookie
    return request.headers.get("Authorization-Refresh")


def _refresh_cookie_secure(request: Request) -> bool:
    return settings.is_production or request.url.scheme == "https"


def _refresh_cookie_max_age() -> int:
    return settings.jwt_refresh_token_expire_days * 24 * 3600


def _set_refresh_cookie(
    response: Response,
    request: Request,
    refresh_token: str,
) -> None:
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=_refresh_cookie_secure(request),
        samesite="lax",
        max_age=_refresh_cookie_max_age(),
        path="/api/v1/auth",
    )


def _delete_refresh_cookie(response: Response, request: Request) -> None:
    response.delete_cookie(
        key="refresh_token",
        path="/api/v1/auth",
        httponly=True,
        secure=_refresh_cookie_secure(request),
        samesite="lax",
    )


@router.post("/login", response_model=TokenResponse)
async def login(
    body: LoginRequest,
    request: Request,
    response: Response,
    db: DBSession,
) -> TokenResponse:
    service = _get_auth_service(db)
    device_info = get_device_info(request)
    result = await service.login(body.email, body.password, device_info)

    _set_refresh_cookie(response, request, result["refresh_token"])

    return TokenResponse(
        access_token=result["access_token"],
        refresh_token=result["refresh_token"],
        refresh_expires_at=result["refresh_expires_at"],
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    request: Request,
    response: Response,
    db: DBSession,
    refresh_token_cookie: Annotated[str | None, Cookie(alias="refresh_token")] = None,
) -> TokenResponse:
    raw_token = refresh_token_cookie or request.headers.get("Authorization-Refresh")
    if not raw_token:
        from app.core.exceptions import UnauthorizedError

        raise UnauthorizedError(message="Refresh token not provided")

    service = _get_auth_service(db)
    device_info = get_device_info(request)
    result = await service.refresh(raw_token, device_info)

    _set_refresh_cookie(response, request, result["refresh_token"])

    return TokenResponse(
        access_token=result["access_token"],
        refresh_token=result["refresh_token"],
        refresh_expires_at=result["refresh_expires_at"],
    )


@router.post("/logout", status_code=204)
async def logout(
    request: Request,
    response: Response,
    db: DBSession,
    refresh_token_cookie: Annotated[str | None, Cookie(alias="refresh_token")] = None,
) -> None:
    raw_token = refresh_token_cookie or request.headers.get("Authorization-Refresh")
    if raw_token:
        service = _get_auth_service(db)
        await service.logout(raw_token)
    _delete_refresh_cookie(response, request)


@router.post("/logout-all", status_code=204)
async def logout_all(
    request: Request,
    response: Response,
    user: CurrentUser,
    db: DBSession,
) -> None:
    service = _get_auth_service(db)
    await service.logout_all(user.id)
    _delete_refresh_cookie(response, request)


@router.get("/me")
async def get_me(
    user: CurrentUser,
    employee: CurrentEmployee,
) -> dict[str, Any]:
    return {
        "id": str(user.id),
        "email": user.email,
        "is_active": user.is_active,
        "employee": {
            "id": str(employee.id),
            "personnel_number": employee.personnel_number,
            "first_name": employee.first_name,
            "last_name": employee.last_name,
            "middle_name": employee.middle_name,
            "role": employee.role,
            "department_id": str(employee.department_id),
            "position_id": str(employee.position_id),
            "avatar_url": employee.avatar_url,
        },
    }


@router.get("/sessions", response_model=list[SessionResponse])
async def list_sessions(
    user: CurrentUser,
    db: DBSession,
) -> list[SessionResponse]:
    service = _get_auth_service(db)
    sessions = await service.get_sessions(user.id)
    return [
        SessionResponse(
            id=s.id,
            device_info=s.device_info,
            created_at=s.created_at,
            expires_at=s.expires_at,
        )
        for s in sessions
    ]


@router.delete("/sessions/{session_id}", status_code=204)
async def revoke_session(
    session_id: uuid.UUID,
    user: CurrentUser,
    db: DBSession,
) -> None:
    service = _get_auth_service(db)
    await service.revoke_session(user.id, session_id)


@router.post("/change-password", status_code=204)
async def change_password(
    body: ChangePasswordRequest,
    request: Request,
    response: Response,
    user: CurrentUser,
    db: DBSession,
) -> None:
    service = _get_auth_service(db)
    await service.change_password(user.id, body.current_password, body.new_password)
    _delete_refresh_cookie(response, request)
