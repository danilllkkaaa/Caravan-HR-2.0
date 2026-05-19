from __future__ import annotations

from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


class AppError(Exception):
    """Base application error."""

    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    code: str = "INTERNAL_ERROR"
    message: str = "An internal error occurred"

    def __init__(
        self,
        message: str | None = None,
        details: dict[str, Any] | None = None,
        code: str | None = None,
    ) -> None:
        self.message = message or self.__class__.message
        self.details = details or {}
        if code:
            self.code = code
        super().__init__(self.message)


class NotFoundError(AppError):
    status_code = status.HTTP_404_NOT_FOUND
    code = "NOT_FOUND"
    message = "Resource not found"


class UnauthorizedError(AppError):
    status_code = status.HTTP_401_UNAUTHORIZED
    code = "UNAUTHORIZED"
    message = "Authentication required"


class ForbiddenError(AppError):
    status_code = status.HTTP_403_FORBIDDEN
    code = "FORBIDDEN"
    message = "Access denied"


class ConflictError(AppError):
    status_code = status.HTTP_409_CONFLICT
    code = "CONFLICT"
    message = "Resource conflict"


class ValidationError(AppError):
    status_code = status.HTTP_422_UNPROCESSABLE_CONTENT
    code = "VALIDATION_ERROR"
    message = "Validation failed"


class AccountLockedError(AppError):
    status_code = 423
    code = "ACCOUNT_LOCKED"
    message = "Account is locked due to too many failed login attempts"


class InvalidCredentialsError(AppError):
    status_code = status.HTTP_401_UNAUTHORIZED
    code = "INVALID_CREDENTIALS"
    message = "Invalid email or password"


class TokenExpiredError(AppError):
    status_code = status.HTTP_401_UNAUTHORIZED
    code = "TOKEN_EXPIRED"
    message = "Token has expired"


class TokenRevokedError(AppError):
    status_code = status.HTTP_401_UNAUTHORIZED
    code = "TOKEN_REVOKED"
    message = "Token has been revoked"


class VacationOverlapError(AppError):
    status_code = status.HTTP_409_CONFLICT
    code = "VACATION_OVERLAP"
    message = "Vacation dates overlap with existing request"


class InsufficientBalanceError(AppError):
    status_code = status.HTTP_409_CONFLICT
    code = "INSUFFICIENT_BALANCE"
    message = "Insufficient vacation balance"


class InvalidDateRangeError(AppError):
    status_code = status.HTTP_400_BAD_REQUEST
    code = "INVALID_DATE_RANGE"
    message = "End date must be on or after start date"


class VacationTypeNotFoundError(AppError):
    status_code = status.HTTP_404_NOT_FOUND
    code = "VACATION_TYPE_NOT_FOUND"
    message = "Vacation type not found"


def _error_response(
    status_code: int,
    code: str,
    message: str,
    details: dict[str, Any] | None = None,
) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={"error": {"code": code, "message": message, "details": details or {}}},
    )


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
        return _error_response(exc.status_code, exc.code, exc.message, exc.details)

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        details = {"errors": exc.errors()}
        return _error_response(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            "VALIDATION_ERROR",
            "Request validation failed",
            details,
        )

    @app.exception_handler(status.HTTP_404_NOT_FOUND)
    async def not_found_handler(request: Request, exc: Exception) -> JSONResponse:
        return _error_response(
            status.HTTP_404_NOT_FOUND, "NOT_FOUND", "The requested resource was not found"
        )

    @app.exception_handler(status.HTTP_405_METHOD_NOT_ALLOWED)
    async def method_not_allowed_handler(request: Request, exc: Exception) -> JSONResponse:
        return _error_response(
            status.HTTP_405_METHOD_NOT_ALLOWED,
            "METHOD_NOT_ALLOWED",
            "Method not allowed",
        )

    @app.exception_handler(Exception)
    async def generic_error_handler(request: Request, exc: Exception) -> JSONResponse:
        import structlog

        log = structlog.get_logger(__name__)
        log.exception("Unhandled exception", exc_info=exc)
        return _error_response(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "INTERNAL_ERROR",
            "An internal server error occurred",
        )
