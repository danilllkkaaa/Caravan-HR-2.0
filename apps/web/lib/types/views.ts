/** View models aligned with the Stage 2 backend API (UUID ids, snake_case sources). */

export interface VacationTypeView {
  id: string;
  code: string;
  name: string;
  isPaid: boolean;
  requiresDocuments: boolean;
}

export interface VacationBalanceView {
  year: number;
  totalDays: number;
  usedDays: number;
  availableDays: number;
}

export interface EmployeeSummaryView {
  id: string;
  firstName: string;
  lastName: string;
  fullName: string;
  personnelNumber: string;
  avatarUrl: string | null;
  role: string;
}

export interface VacationRequestView {
  id: string;
  employeeId: string;
  vacationTypeId: string;
  vacationType: VacationTypeView;
  startDate: string;
  endDate: string;
  daysCount: number;
  status: string;
  comment: string | null;
  rejectionReason: string | null;
  approverId: string | null;
  approvedAt: string | null;
  createdAt: string;
  updatedAt: string;
  employee?: EmployeeSummaryView;
  warnings?: Record<string, string>;
}

export interface NotificationView {
  id: string;
  type: string;
  title: string;
  body: string;
  isRead: boolean;
  readAt: string | null;
  payload: Record<string, unknown> | null;
  createdAt: string;
}

export interface DashboardView {
  employee: {
    id: string;
    firstName: string;
    lastName: string;
    fullName: string;
    role: string;
    avatarUrl: string | null;
  };
  vacationBalance: VacationBalanceView;
  recentNotifications: NotificationView[];
  generatedAt: string;
}

export interface OffsetList<T> {
  items: T[];
  total: number;
  offset: number;
  limit: number;
}
