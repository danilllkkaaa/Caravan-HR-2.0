import type { TimesheetEntry, TimesheetMonth, TimesheetStatus } from '@corp-portal/shared-types';
import { apiGet, apiPost } from './client';

interface RawTimesheetEntry {
  id: string;
  employee_id: string;
  date: string;
  first_entry_at: string | null;
  last_exit_at: string | null;
  worked_minutes: number;
  status: TimesheetStatus;
  schedule_minutes: number | null;
  created_at: string;
  updated_at: string;
}

interface TimesheetListResponse {
  items: RawTimesheetEntry[];
  date_from: string;
  date_to: string;
}

function toDateOnly(date: Date) {
  return date.toISOString().slice(0, 10);
}

function monthRange(year: number, month: number) {
  const start = new Date(Date.UTC(year, month - 1, 1));
  const end = new Date(Date.UTC(year, month, 0));
  return { date_from: toDateOnly(start), date_to: toDateOnly(end) };
}

function mapEntry(row: RawTimesheetEntry): TimesheetEntry {
  const overtimeMinutes = Math.max(
    0,
    row.worked_minutes - (row.schedule_minutes ?? row.worked_minutes)
  );
  return {
    id: row.id,
    employeeId: row.employee_id,
    date: row.date,
    status: row.status,
    checkIn: row.first_entry_at,
    checkOut: row.last_exit_at,
    hoursWorked: row.worked_minutes / 60,
    overtimeHours: overtimeMinutes > 0 ? overtimeMinutes / 60 : null,
    locationId: null,
    location: null,
    note: null,
    isManualEntry: false,
    approvedById: null,
    approvedAt: null,
    createdAt: row.created_at,
    updatedAt: row.updated_at,
  };
}

function buildSummary(entries: TimesheetEntry[]): TimesheetMonth['summary'] {
  const byStatus = (status: TimesheetStatus) =>
    entries.filter((entry) => entry.status === status).length;
  const workedDays =
    byStatus('work' as TimesheetStatus) + byStatus('overtime' as TimesheetStatus);

  return {
    totalWorkingDays: entries.length,
    presentDays: workedDays,
    absentDays: byStatus('absence' as TimesheetStatus),
    vacationDays: byStatus('vacation' as TimesheetStatus),
    sickLeaveDays: byStatus('sick' as TimesheetStatus),
    holidayDays: byStatus('holiday' as TimesheetStatus),
    totalHoursWorked: entries.reduce((sum, entry) => sum + (entry.hoursWorked ?? 0), 0),
    totalOvertimeHours: entries.reduce((sum, entry) => sum + (entry.overtimeHours ?? 0), 0),
    attendanceRate: entries.length ? Math.round((workedDays / entries.length) * 100) : 0,
  };
}

async function getEntries(date_from: string, date_to: string) {
  const raw = await apiGet<TimesheetListResponse>('/timesheet', {
    params: { date_from, date_to },
  });
  return (raw.items ?? []).map(mapEntry);
}

export const timesheetApi = {
  getMonth: async (year: number, month: number): Promise<TimesheetMonth> => {
    const range = monthRange(year, month);
    const entries = await getEntries(range.date_from, range.date_to);
    return { year, month, entries, summary: buildSummary(entries) };
  },

  getByDate: async (date: string): Promise<TimesheetEntry | null> => {
    const entries = await getEntries(date, date);
    return entries[0] ?? null;
  },

  getRange: (startDate: string, endDate: string): Promise<TimesheetEntry[]> =>
    getEntries(startDate, endDate),

  upsertEntry: (data: {
    employeeId?: string;
    date: string;
    checkIn?: string;
    checkOut?: string;
    note?: string;
  }) => apiPost<TimesheetEntry>('/timesheet/entries', data),

  checkIn: () => apiPost<TimesheetEntry>('/timesheet/check-in'),

  checkOut: () => apiPost<TimesheetEntry>('/timesheet/check-out'),

  getTeamMonth: async (
    _year: number,
    _month: number
  ): Promise<
    Array<{ employee: { id: string; fullName: string }; summary: TimesheetMonth['summary'] }>
  > => [],
};
