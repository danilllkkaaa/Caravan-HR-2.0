from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any
from uuid import UUID

import sentry_sdk
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_fastapi_instrumentator import Instrumentator
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.redis import RedisIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
from starlette.middleware.sessions import SessionMiddleware

from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.exceptions import register_exception_handlers
from app.core.logging import configure_logging, get_logger
from app.infrastructure.database import close_db, close_redis, get_engine, get_redis

configure_logging()
settings = get_settings()
log = get_logger(__name__)


if settings.sentry_dsn:
    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        integrations=[
            FastApiIntegration(),
            SqlalchemyIntegration(),
            RedisIntegration(),
        ],
        traces_sample_rate=settings.sentry_traces_sample_rate,
        environment=settings.sentry_environment,
        release="caravan-hr-api@2.0.0",
    )


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    log.info("Starting up Caravan HR API", env=settings.app_env)
    # Warm up connections
    redis = get_redis()
    try:
        await redis.ping()
        log.info("Redis connection OK")
    except Exception as e:
        log.warning("Redis connection failed on startup", error=str(e))
    yield
    log.info("Shutting down Caravan HR API")
    await close_db()
    await close_redis()


def create_app() -> FastAPI:
    app = FastAPI(
        title="Caravan HR API",
        version="2.0.0",
        description="Corporate HR portal backend API",
        docs_url="/docs" if not settings.is_production else None,
        redoc_url="/redoc" if not settings.is_production else None,
        openapi_url="/openapi.json" if not settings.is_production else None,
        default_response_class=JSONResponse,
        lifespan=lifespan,
    )

    # CORS
    app.add_middleware(
        SessionMiddleware,
        secret_key=settings.app_secret_key,
        same_site="lax",
        https_only=settings.is_production,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.app_allowed_origins,
        allow_origin_regex=settings.cors_allowed_origin_regex,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Total-Count"],
    )

    # Request ID middleware
    @app.middleware("http")
    async def request_id_middleware(request: Request, call_next):
        import uuid

        import structlog

        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(
            request_id=request_id,
            method=request.method,
            path=request.url.path,
        )
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response

    # Register exception handlers
    register_exception_handlers(app)

    # Prometheus metrics
    Instrumentator(
        should_group_status_codes=False,
        should_ignore_untemplated=True,
        should_group_untemplated=True,
        excluded_handlers=["/health", "/health/ready", "/metrics"],
    ).instrument(app).expose(app, endpoint="/metrics", include_in_schema=False)

    # Routers
    app.include_router(api_router)
    _setup_sqladmin(app)

    # Health endpoints
    @app.get("/health", tags=["health"], include_in_schema=False)
    @app.get("/api/v1/health", tags=["health"], include_in_schema=False)
    async def health() -> dict[str, str]:
        return {"status": "ok", "version": "2.0.0"}

    @app.get("/health/ready", tags=["health"], include_in_schema=False, response_model=None)
    @app.get("/api/v1/health/ready", tags=["health"], include_in_schema=False, response_model=None)
    async def health_ready() -> Any:
        from sqlalchemy import text

        from app.infrastructure.database import get_redis

        issues: list[str] = []

        try:
            async with get_engine().connect() as conn:
                await conn.execute(text("SELECT 1"))
        except Exception as e:
            issues.append(f"db: {e}")

        try:
            redis = get_redis()
            await redis.ping()
        except Exception as e:
            issues.append(f"redis: {e}")

        if issues:
            return JSONResponse(
                status_code=503,
                content={"status": "not_ready", "issues": issues},
            )
        return {"status": "ready"}

    return app


def _setup_sqladmin(app: FastAPI) -> None:
    """Mount SQLAdmin for the stage-1 admin UI."""
    from sqladmin import Admin, ModelView
    from sqladmin.authentication import AuthenticationBackend

    from app.core.security import verify_password
    from app.infrastructure.database import get_session_factory
    from app.infrastructure.models import (
        AuditLog,
        Department,
        Employee,
        Position,
        RefreshToken,
        User,
        VacationBalance,
        VacationRequest,
        VacationType,
        WorkLocation,
    )
    from app.infrastructure.repositories.employee import EmployeeRepository
    from app.infrastructure.repositories.user import UserRepository

    class AdminAuth(AuthenticationBackend):
        async def login(self, request: Request) -> bool:
            form = await request.form()
            email = str(form.get("username") or form.get("email") or "")
            password = str(form.get("password") or "")

            async with get_session_factory()() as session:
                user = await UserRepository(session).get_by_email(email)
                if user is None or not user.is_active:
                    return False
                if not verify_password(password, user.password_hash):
                    return False

                employee = await EmployeeRepository(session).get_by_user_id(user.id)
                if employee is None or employee.role != "admin":
                    return False

                request.session.update({"sqladmin_user_id": str(user.id)})
                return True

        async def logout(self, request: Request) -> bool:
            request.session.clear()
            return True

        async def authenticate(self, request: Request) -> bool:
            user_id = request.session.get("sqladmin_user_id")
            if not user_id:
                return False

            try:
                parsed_user_id = UUID(user_id)
            except ValueError:
                request.session.clear()
                return False

            async with get_session_factory()() as session:
                user = await UserRepository(session).get_by_id(parsed_user_id)
                if user is None or not user.is_active:
                    request.session.clear()
                    return False

                employee = await EmployeeRepository(session).get_by_user_id(user.id)
                if employee is None or employee.role != "admin":
                    request.session.clear()
                    return False

            return True

    class UserAdmin(ModelView, model=User):
        column_list = [User.id, User.email, User.is_active, User.created_at, User.updated_at]
        column_searchable_list = [User.email]
        column_sortable_list = [User.email, User.created_at]
        form_excluded_columns = [User.password_hash, User.refresh_tokens, User.employee]

    class EmployeeAdmin(ModelView, model=Employee):
        column_list = [
            Employee.id,
            Employee.personnel_number,
            Employee.last_name,
            Employee.first_name,
            Employee.role,
            Employee.department_id,
            Employee.position_id,
        ]
        column_searchable_list = [
            Employee.personnel_number,
            Employee.last_name,
            Employee.first_name,
        ]
        column_sortable_list = [Employee.last_name, Employee.hire_date]

    class DepartmentAdmin(ModelView, model=Department):
        column_list = [
            Department.id,
            Department.external_id_1c,
            Department.name,
            Department.parent_id,
        ]
        column_searchable_list = [Department.name, Department.external_id_1c]

    class PositionAdmin(ModelView, model=Position):
        column_list = [Position.id, Position.external_id_1c, Position.name]
        column_searchable_list = [Position.name, Position.external_id_1c]

    class WorkLocationAdmin(ModelView, model=WorkLocation):
        column_list = [
            WorkLocation.id,
            WorkLocation.external_id_1c,
            WorkLocation.name,
            WorkLocation.city,
        ]
        column_searchable_list = [WorkLocation.name, WorkLocation.city]

    class VacationTypeAdmin(ModelView, model=VacationType):
        column_list = [VacationType.id, VacationType.code, VacationType.name, VacationType.is_paid]

    class VacationBalanceAdmin(ModelView, model=VacationBalance):
        column_list = [
            VacationBalance.id,
            VacationBalance.employee_id,
            VacationBalance.year,
            VacationBalance.total_days,
            VacationBalance.used_days,
        ]

    class VacationRequestAdmin(ModelView, model=VacationRequest):
        column_list = [
            VacationRequest.id,
            VacationRequest.employee_id,
            VacationRequest.start_date,
            VacationRequest.end_date,
            VacationRequest.status,
        ]

    class RefreshTokenAdmin(ModelView, model=RefreshToken):
        column_list = [
            RefreshToken.id,
            RefreshToken.user_id,
            RefreshToken.expires_at,
            RefreshToken.revoked_at,
            RefreshToken.created_at,
        ]
        can_create = False
        can_edit = False

    class AuditLogAdmin(ModelView, model=AuditLog):
        column_list = [
            AuditLog.id,
            AuditLog.actor_id,
            AuditLog.action,
            AuditLog.target_type,
            AuditLog.target_id,
            AuditLog.created_at,
        ]
        can_create = False
        can_edit = False

    admin = Admin(
        app,
        get_engine(),
        base_url="/admin/ui",
        authentication_backend=AdminAuth(secret_key=settings.app_secret_key),
        title="Caravan HR Admin",
    )
    admin.add_view(UserAdmin)
    admin.add_view(EmployeeAdmin)
    admin.add_view(DepartmentAdmin)
    admin.add_view(PositionAdmin)
    admin.add_view(WorkLocationAdmin)
    admin.add_view(VacationTypeAdmin)
    admin.add_view(VacationBalanceAdmin)
    admin.add_view(VacationRequestAdmin)
    admin.add_view(RefreshTokenAdmin)
    admin.add_view(AuditLogAdmin)


app = create_app()
