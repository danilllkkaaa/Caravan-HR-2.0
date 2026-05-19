"""Initial migration - all tables, enums, indexes

Revision ID: 0001
Revises:
Create Date: 2026-05-18 00:00:00.000000
"""
from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ---------------------------------------------------------------------------
    # Install extensions
    # ---------------------------------------------------------------------------
    op.execute("CREATE EXTENSION IF NOT EXISTS citext")
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")

    # ---------------------------------------------------------------------------
    # Enums
    # ---------------------------------------------------------------------------
    op.execute(
        "CREATE TYPE employee_role AS ENUM ('employee', 'manager', 'hr', 'admin')"
    )
    op.execute("CREATE TYPE sync_source AS ENUM ('1c', 'manual')")
    op.execute(
        "CREATE TYPE vacation_status AS ENUM ('draft', 'pending', 'approved', 'rejected', 'cancelled')"
    )
    op.execute("CREATE TYPE sick_leave_status AS ENUM ('open', 'closed')")
    op.execute("CREATE TYPE attendance_event_type AS ENUM ('entry', 'exit')")
    op.execute(
        "CREATE TYPE timesheet_status AS ENUM ('work', 'overtime', 'partial', 'weekend', 'holiday', 'absence', 'vacation', 'sick')"
    )
    op.execute(
        "CREATE TYPE notification_type AS ENUM ('approved', 'rejected', 'info', 'reminder', 'sharepoint_link')"
    )

    # ---------------------------------------------------------------------------
    # users
    # ---------------------------------------------------------------------------
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, default=sa.text("uuid_generate_v4()")),
        sa.Column("email", sa.String(320), nullable=False, unique=True),
        sa.Column("password_hash", sa.Text, nullable=False),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.Column("failed_login_attempts", sa.Integer, nullable=False, server_default=sa.text("0")),
        sa.Column("locked_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_users_email", "users", ["email"])

    # ---------------------------------------------------------------------------
    # departments (without head_id FK yet - employees table not created)
    # ---------------------------------------------------------------------------
    op.create_table(
        "departments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, default=sa.text("uuid_generate_v4()")),
        sa.Column("external_id_1c", sa.String(64), nullable=False, unique=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("parent_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("departments.id"), nullable=True),
        sa.Column("head_id", postgresql.UUID(as_uuid=True), nullable=True),  # FK added later
    )
    op.create_index("uq_departments_external_id_1c", "departments", ["external_id_1c"], unique=True)

    # ---------------------------------------------------------------------------
    # positions
    # ---------------------------------------------------------------------------
    op.create_table(
        "positions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, default=sa.text("uuid_generate_v4()")),
        sa.Column("external_id_1c", sa.String(64), nullable=False, unique=True),
        sa.Column("name", sa.String(255), nullable=False),
    )
    op.create_index("uq_positions_external_id_1c", "positions", ["external_id_1c"], unique=True)

    # ---------------------------------------------------------------------------
    # work_locations (without hr_employee_id FK yet)
    # ---------------------------------------------------------------------------
    op.create_table(
        "work_locations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, default=sa.text("uuid_generate_v4()")),
        sa.Column("external_id_1c", sa.String(64), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("city", sa.String(128), nullable=False),
        sa.Column("hr_employee_id", postgresql.UUID(as_uuid=True), nullable=True),  # FK added later
    )

    # ---------------------------------------------------------------------------
    # employees
    # ---------------------------------------------------------------------------
    op.create_table(
        "employees",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, default=sa.text("uuid_generate_v4()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False, unique=True),
        sa.Column("external_id_1c", sa.String(64), nullable=False),
        sa.Column("personnel_number", sa.String(32), nullable=False),
        sa.Column("first_name", sa.String(255), nullable=False),
        sa.Column("last_name", sa.String(255), nullable=False),
        sa.Column("middle_name", sa.String(255), nullable=False, server_default=""),
        sa.Column("birth_date", sa.Date, nullable=True),
        sa.Column("phone", sa.String(32), nullable=False, server_default=""),
        sa.Column("department_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("departments.id"), nullable=False),
        sa.Column("position_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("positions.id"), nullable=False),
        sa.Column("manager_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("employees.id"), nullable=True),
        sa.Column("role", postgresql.ENUM("employee", "manager", "hr", "admin", name="employee_role", create_type=False), nullable=False, server_default="employee"),
        sa.Column("hire_date", sa.Date, nullable=False),
        sa.Column("work_location_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("work_locations.id"), nullable=True),
        sa.Column("avatar_url", sa.Text, nullable=True),
        sa.Column("sync_hash", sa.String(64), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_employees_external_id_1c", "employees", ["external_id_1c"])
    op.create_index("ix_employees_personnel_number", "employees", ["personnel_number"])
    op.create_index("ix_employees_department_id", "employees", ["department_id"])
    op.create_index("ix_employees_manager_id", "employees", ["manager_id"])
    op.create_index("ix_employees_work_location_id", "employees", ["work_location_id"])

    # Now add the deferred FKs
    op.create_foreign_key("fk_departments_head_id", "departments", "employees", ["head_id"], ["id"])
    op.create_foreign_key("fk_work_locations_hr_employee_id", "work_locations", "employees", ["hr_employee_id"], ["id"])

    # ---------------------------------------------------------------------------
    # vacation_types
    # ---------------------------------------------------------------------------
    op.create_table(
        "vacation_types",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, default=sa.text("uuid_generate_v4()")),
        sa.Column("code", sa.String(64), nullable=False, unique=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("is_paid", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.Column("requires_documents", sa.Boolean, nullable=False, server_default=sa.text("false")),
    )

    # ---------------------------------------------------------------------------
    # vacation_balances
    # ---------------------------------------------------------------------------
    op.create_table(
        "vacation_balances",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, default=sa.text("uuid_generate_v4()")),
        sa.Column("employee_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("employees.id"), nullable=False),
        sa.Column("year", sa.Integer, nullable=False),
        sa.Column("total_days", sa.Numeric(5, 2), nullable=False, server_default=sa.text("0")),
        sa.Column("used_days", sa.Numeric(5, 2), nullable=False, server_default=sa.text("0")),
        sa.Column("sync_source", postgresql.ENUM("1c", "manual", name="sync_source", create_type=False), nullable=False, server_default="manual"),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("employee_id", "year", name="uq_vacation_balances_employee_year"),
    )
    op.create_index("ix_vacation_balances_employee_year", "vacation_balances", ["employee_id", "year"])

    # ---------------------------------------------------------------------------
    # vacation_requests
    # ---------------------------------------------------------------------------
    op.create_table(
        "vacation_requests",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, default=sa.text("uuid_generate_v4()")),
        sa.Column("employee_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("employees.id"), nullable=False),
        sa.Column("vacation_type_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("vacation_types.id"), nullable=False),
        sa.Column("start_date", sa.Date, nullable=False),
        sa.Column("end_date", sa.Date, nullable=False),
        sa.Column("days_count", sa.Integer, nullable=False),
        sa.Column("comment", sa.Text, nullable=True),
        sa.Column("status", postgresql.ENUM("draft", "pending", "approved", "rejected", "cancelled", name="vacation_status", create_type=False), nullable=False, server_default="draft"),
        sa.Column("approver_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("employees.id"), nullable=True),
        sa.Column("approver_comment", sa.Text, nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_vacation_requests_employee_status", "vacation_requests", ["employee_id", "status"])
    op.create_index("ix_vacation_requests_dates", "vacation_requests", ["start_date", "end_date"])
    op.create_index("ix_vacation_requests_approver", "vacation_requests", ["approver_id"])

    # ---------------------------------------------------------------------------
    # sick_leaves
    # ---------------------------------------------------------------------------
    op.create_table(
        "sick_leaves",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, default=sa.text("uuid_generate_v4()")),
        sa.Column("employee_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("employees.id"), nullable=False),
        sa.Column("start_date", sa.Date, nullable=False),
        sa.Column("end_date", sa.Date, nullable=True),
        sa.Column("open_comment", sa.Text, nullable=True),
        sa.Column("close_comment", sa.Text, nullable=True),
        sa.Column("document_url", sa.Text, nullable=True),
        sa.Column("status", postgresql.ENUM("open", "closed", name="sick_leave_status", create_type=False), nullable=False, server_default="open"),
        sa.Column("closed_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("employees.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_sick_leaves_employee_status", "sick_leaves", ["employee_id", "status"])

    # ---------------------------------------------------------------------------
    # attendance_events
    # ---------------------------------------------------------------------------
    op.create_table(
        "attendance_events",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("employee_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("employees.id"), nullable=True),
        sa.Column("hikvision_person_id", sa.String(255), nullable=False),
        sa.Column("event_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("event_type", postgresql.ENUM("entry", "exit", name="attendance_event_type", create_type=False), nullable=False),
        sa.Column("device_id", sa.String(255), nullable=False),
        sa.Column("raw_payload", postgresql.JSONB, nullable=False, server_default=sa.text("'{}'")),
        sa.Column("processed", sa.Boolean, nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_attendance_events_employee_at", "attendance_events", ["employee_id", "event_at"])
    op.create_index("ix_attendance_events_processed", "attendance_events", ["processed"])
    op.create_index("ix_attendance_events_hikvision_person_id", "attendance_events", ["hikvision_person_id"])

    # ---------------------------------------------------------------------------
    # timesheet_entries
    # ---------------------------------------------------------------------------
    op.create_table(
        "timesheet_entries",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, default=sa.text("uuid_generate_v4()")),
        sa.Column("employee_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("employees.id"), nullable=False),
        sa.Column("date", sa.Date, nullable=False),
        sa.Column("first_entry_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_exit_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("worked_minutes", sa.Integer, nullable=False, server_default=sa.text("0")),
        sa.Column("status", postgresql.ENUM("work", "overtime", "partial", "weekend", "holiday", "absence", "vacation", "sick", name="timesheet_status", create_type=False), nullable=False, server_default="work"),
        sa.Column("schedule_minutes", sa.Integer, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("employee_id", "date", name="uq_timesheet_employee_date"),
    )
    op.create_index("ix_timesheet_entries_employee_date", "timesheet_entries", ["employee_id", "date"])

    # ---------------------------------------------------------------------------
    # notifications
    # ---------------------------------------------------------------------------
    op.create_table(
        "notifications",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, default=sa.text("uuid_generate_v4()")),
        sa.Column("employee_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("employees.id"), nullable=False),
        sa.Column("type", postgresql.ENUM("approved", "rejected", "info", "reminder", "sharepoint_link", name="notification_type", create_type=False), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("body", sa.Text, nullable=False),
        sa.Column("payload", postgresql.JSONB, nullable=True),
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_notifications_employee_read", "notifications", ["employee_id", "read_at"])
    op.create_index("ix_notifications_created_at", "notifications", ["created_at"])

    # ---------------------------------------------------------------------------
    # refresh_tokens
    # ---------------------------------------------------------------------------
    op.create_table(
        "refresh_tokens",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, default=sa.text("uuid_generate_v4()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("token_hash", sa.String(64), nullable=False, unique=True),
        sa.Column("device_info", postgresql.JSONB, nullable=False, server_default=sa.text("'{}'")),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_refresh_tokens_token_hash", "refresh_tokens", ["token_hash"], unique=True)
    op.create_index("ix_refresh_tokens_user_revoked", "refresh_tokens", ["user_id", "revoked_at"])
    op.create_index("ix_refresh_tokens_expires_at", "refresh_tokens", ["expires_at"])

    # ---------------------------------------------------------------------------
    # audit_log
    # ---------------------------------------------------------------------------
    op.create_table(
        "audit_log",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("actor_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("action", sa.String(255), nullable=False),
        sa.Column("target_type", sa.String(255), nullable=False),
        sa.Column("target_id", sa.String(255), nullable=False),
        sa.Column("changes", postgresql.JSONB, nullable=False, server_default=sa.text("'{}'")),
        sa.Column("ip", postgresql.INET, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_audit_log_actor", "audit_log", ["actor_id"])
    op.create_index("ix_audit_log_target", "audit_log", ["target_type", "target_id"])
    op.create_index("ix_audit_log_created_at", "audit_log", ["created_at"])

    # ---------------------------------------------------------------------------
    # Triggers: auto-update updated_at
    # ---------------------------------------------------------------------------
    op.execute("""
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = now();
            RETURN NEW;
        END;
        $$ language 'plpgsql';
    """)

    for table in ["users", "employees", "vacation_requests", "sick_leaves", "timesheet_entries"]:
        op.execute(f"""
            CREATE TRIGGER trg_{table}_updated_at
            BEFORE UPDATE ON {table}
            FOR EACH ROW EXECUTE PROCEDURE update_updated_at_column();
        """)

    # ---------------------------------------------------------------------------
    # Seed vacation types
    # ---------------------------------------------------------------------------
    op.execute("""
        INSERT INTO vacation_types (id, code, name, is_paid, requires_documents) VALUES
        (uuid_generate_v4(), 'ANNUAL', 'Annual Leave', true, false),
        (uuid_generate_v4(), 'SICK', 'Sick Leave', true, true),
        (uuid_generate_v4(), 'UNPAID', 'Unpaid Leave', false, false),
        (uuid_generate_v4(), 'STUDY', 'Study Leave', true, true),
        (uuid_generate_v4(), 'MATERNITY', 'Maternity Leave', true, true)
        ON CONFLICT (code) DO NOTHING;
    """)


def downgrade() -> None:
    # Drop triggers
    for table in ["users", "employees", "vacation_requests", "sick_leaves", "timesheet_entries"]:
        op.execute(f"DROP TRIGGER IF EXISTS trg_{table}_updated_at ON {table}")

    op.execute("DROP FUNCTION IF EXISTS update_updated_at_column()")

    # Drop tables in reverse dependency order
    for table in [
        "audit_log",
        "refresh_tokens",
        "notifications",
        "timesheet_entries",
        "attendance_events",
        "sick_leaves",
        "vacation_requests",
        "vacation_balances",
        "vacation_types",
        "employees",
        "work_locations",
        "positions",
        "departments",
        "users",
    ]:
        op.execute(f"DROP TABLE IF EXISTS {table} CASCADE")

    for enum_type in [
        "employee_role",
        "sync_source",
        "vacation_status",
        "sick_leave_status",
        "attendance_event_type",
        "timesheet_status",
        "notification_type",
    ]:
        op.execute(f"DROP TYPE IF EXISTS {enum_type}")

