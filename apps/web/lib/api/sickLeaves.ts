import type {
  CloseSickLeaveRequest,
  CreateSickLeaveRequest,
  PaginatedResponse,
  SickLeave,
  SickLeaveStatus,
} from '@corp-portal/shared-types';
import { apiGet, apiPost } from './client';

interface ListSickLeavesParams {
  page?: number;
  pageSize?: number;
  status?: SickLeaveStatus;
  year?: number;
}

function mapSickLeave(row: any): SickLeave {
  const start = new Date(row.start_date);
  const end = row.end_date ? new Date(row.end_date) : null;
  const calendarDays = end
    ? Math.floor((end.getTime() - start.getTime()) / 86_400_000) + 1
    : null;

  return {
    id: row.id,
    employeeId: row.employee_id,
    startDate: row.start_date,
    endDate: row.end_date ?? null,
    calendarDays,
    workingDays: null,
    status: row.status,
    diagnosisCode: null,
    documentNumber: null,
    documentUrl: row.document_url ?? null,
    comment: row.close_comment ?? row.open_comment ?? null,
    closedById: row.closed_by ?? null,
    closedAt: row.status === 'closed' ? row.updated_at : null,
    createdAt: row.created_at,
    updatedAt: row.updated_at,
  };
}

function createBody(data: CreateSickLeaveRequest) {
  return {
    start_date: data.startDate,
    comment: data.comment,
  };
}

function closeBody(data: CloseSickLeaveRequest) {
  return {
    end_date: data.endDate,
    comment: data.comment,
  };
}

export const sickLeavesApi = {
  list: async (params?: ListSickLeavesParams): Promise<PaginatedResponse<SickLeave>> => {
    const raw = await apiGet<any>('/sick-leaves', {
      params: {
        offset: ((params?.page ?? 1) - 1) * (params?.pageSize ?? 20),
        limit: params?.pageSize ?? 20,
      },
    });
    const items = (raw.items ?? []).map(mapSickLeave);
    const page = params?.page ?? 1;
    const pageSize = params?.pageSize ?? raw.limit ?? 20;
    const total = raw.total ?? items.length;
    return {
      items: params?.status ? items.filter((item: SickLeave) => item.status === params.status) : items,
      total,
      page,
      pageSize,
      totalPages: Math.max(1, Math.ceil(total / pageSize)),
      hasNext: page * pageSize < total,
      hasPrev: page > 1,
    };
  },

  getById: async (id: string): Promise<SickLeave> => {
    const raw = await apiGet<any>(`/sick-leaves/${id}`);
    return mapSickLeave(raw);
  },

  create: async (data: CreateSickLeaveRequest): Promise<SickLeave> => {
    const raw = await apiPost<any>('/sick-leaves', createBody(data));
    return mapSickLeave(raw);
  },

  close: async (id: string, data: CloseSickLeaveRequest): Promise<SickLeave> => {
    const raw = await apiPost<any>(`/sick-leaves/${id}/close`, closeBody(data));
    return mapSickLeave(raw);
  },

  uploadDocument: async (id: string, file: File) => {
    const filename = encodeURIComponent(file.name);
    const raw = await apiPost<{ upload_url: string; object_url: string }>(
      `/sick-leaves/upload-url?sick_leave_id=${id}&filename=${filename}`
    );
    await fetch(raw.upload_url, { method: 'PUT', body: file });
    const saved = await apiPost<any>(`/sick-leaves/${id}/document`, {
      document_url: raw.object_url,
    });
    return { documentUrl: saved.document_url };
  },

  listAll: async (params?: ListSickLeavesParams): Promise<PaginatedResponse<SickLeave>> =>
    sickLeavesApi.list(params),
};
