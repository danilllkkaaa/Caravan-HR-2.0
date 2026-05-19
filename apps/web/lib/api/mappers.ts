import type {
  DashboardView,
  EmployeeSummaryView,
  NotificationView,
  VacationBalanceView,
  VacationRequestView,
  VacationTypeView,
} from '@/lib/types/views';

interface BackendVacationType {
  id: string;
  code: string;
  name: string;
  is_paid: boolean;
  requires_documents: boolean;
}

interface BackendVacationRequest {
  id: string;
  employee_id: string;
  vacation_type_id: string;
  vacation_type?: BackendVacationType;
  start_date: string;
  end_date: string;
  days_count: number;
  comment: string | null;
  status: string;
  approver_id: string | null;
  approver_comment: string | null;
  approved_at: string | null;
  created_at: string;
  updated_at: string;
  employee?: {
    id: string;
    first_name: string;
    last_name: string;
    full_name: string;
    personnel_number: string;
    avatar_url: string | null;
    role: string;
  };
  warnings?: Record<string, string>;
}

interface BackendNotification {
  id: string;
  type: string;
  title: string;
  body: string;
  read_at: string | null;
  payload: Record<string, unknown> | null;
  created_at: string;
}

interface BackendDashboard {
  employee: {
    id: string;
    first_name: string;
    last_name: string;
    middle_name?: string;
    role: string;
    avatar_url: string | null;
  };
  vacation_balance: {
    year: number;
    total_days: number;
    used_days: number;
    available_days: number;
  };
  recent_notifications: BackendNotification[];
  generated_at: string;
}

function mapVacationType(t: BackendVacationType): VacationTypeView {
  return {
    id: t.id,
    code: t.code,
    name: t.name,
    isPaid: t.is_paid,
    requiresDocuments: t.requires_documents,
  };
}

function fallbackType(id: string): VacationTypeView {
  return {
    id,
    code: 'unknown',
    name: 'Отпуск',
    isPaid: true,
    requiresDocuments: false,
  };
}

export function mapVacationRequest(raw: BackendVacationRequest): VacationRequestView {
  const vtype = raw.vacation_type
    ? mapVacationType(raw.vacation_type)
    : fallbackType(raw.vacation_type_id);

  return {
    id: raw.id,
    employeeId: raw.employee_id,
    vacationTypeId: raw.vacation_type_id,
    vacationType: vtype,
    startDate: raw.start_date,
    endDate: raw.end_date,
    daysCount: raw.days_count,
    status: raw.status,
    comment: raw.comment,
    rejectionReason:
      raw.status === 'rejected' ? raw.approver_comment : null,
    approverId: raw.approver_id,
    approvedAt: raw.approved_at,
    createdAt: raw.created_at,
    updatedAt: raw.updated_at,
    warnings: raw.warnings,
    employee: raw.employee
      ? {
          id: raw.employee.id,
          firstName: raw.employee.first_name,
          lastName: raw.employee.last_name,
          fullName: raw.employee.full_name,
          personnelNumber: raw.employee.personnel_number,
          avatarUrl: raw.employee.avatar_url,
          role: raw.employee.role,
        }
      : undefined,
  };
}

export function mapNotification(raw: BackendNotification): NotificationView {
  return {
    id: raw.id,
    type: raw.type,
    title: raw.title,
    body: raw.body,
    isRead: raw.read_at != null,
    readAt: raw.read_at,
    payload: raw.payload,
    createdAt: raw.created_at,
  };
}

export function mapDashboard(raw: BackendDashboard): DashboardView {
  const first = raw.employee.first_name;
  const last = raw.employee.last_name;
  return {
    employee: {
      id: raw.employee.id,
      firstName: first,
      lastName: last,
      fullName: `${last} ${first}`.trim(),
      role: raw.employee.role,
      avatarUrl: raw.employee.avatar_url,
    },
    vacationBalance: {
      year: raw.vacation_balance.year,
      totalDays: raw.vacation_balance.total_days,
      usedDays: raw.vacation_balance.used_days,
      availableDays: raw.vacation_balance.available_days,
    },
    recentNotifications: raw.recent_notifications.map(mapNotification),
    generatedAt: raw.generated_at,
  };
}

export function mapBalance(raw: {
  year: number;
  total_days: number;
  used_days: number;
  available_days: number;
}): VacationBalanceView {
  return {
    year: raw.year,
    totalDays: raw.total_days,
    usedDays: raw.used_days,
    availableDays: raw.available_days,
  };
}

export type { BackendVacationRequest, BackendNotification, BackendDashboard };
