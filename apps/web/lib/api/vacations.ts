import { apiDelete, apiGet, apiPatch, apiPost } from './client';
import { mapBalance, mapVacationRequest, type BackendVacationRequest } from './mappers';
import type {
  OffsetList,
  VacationBalanceView,
  VacationRequestView,
  VacationTypeView,
} from '@/lib/types/views';

interface ListVacationsParams {
  status?: string;
  year?: number;
  offset?: number;
  limit?: number;
}

interface CreateVacationPayload {
  vacationTypeId: string;
  startDate: string;
  endDate: string;
  comment?: string;
  submit?: boolean;
}

function toCreateBody(data: CreateVacationPayload) {
  return {
    vacation_type_id: data.vacationTypeId,
    start_date: data.startDate,
    end_date: data.endDate,
    comment: data.comment,
    submit: data.submit ?? true,
  };
}

export const vacationsApi = {
  list: async (params?: ListVacationsParams): Promise<OffsetList<VacationRequestView>> => {
    const res = await apiGet<OffsetList<BackendVacationRequest>>('/vacations', {
      params: {
        status: params?.status,
        year: params?.year,
        offset: params?.offset ?? 0,
        limit: params?.limit ?? 20,
      },
    });
    return { ...res, items: res.items.map(mapVacationRequest) };
  },

  getById: async (id: string): Promise<VacationRequestView> => {
    const raw = await apiGet<BackendVacationRequest>(`/vacations/${id}`);
    return mapVacationRequest(raw);
  },

  create: async (data: CreateVacationPayload): Promise<VacationRequestView> => {
    const raw = await apiPost<BackendVacationRequest>('/vacations', toCreateBody(data));
    return mapVacationRequest(raw);
  },

  cancel: (id: string) => apiDelete<void>(`/vacations/${id}`),

  getTypes: async (): Promise<VacationTypeView[]> => {
    const raw = await apiGet<
      Array<{
        id: string;
        code: string;
        name: string;
        is_paid: boolean;
        requires_documents: boolean;
      }>
    >('/vacations/types');
    return raw.map((t) => ({
      id: t.id,
      code: t.code,
      name: t.name,
      isPaid: t.is_paid,
      requiresDocuments: t.requires_documents,
    }));
  },

  getBalance: async (year?: number): Promise<VacationBalanceView> => {
    const raw = await apiGet<{
      year: number;
      total_days: number;
      used_days: number;
      available_days: number;
    }>('/vacations/balance', { params: year ? { year } : undefined });
    return mapBalance(raw);
  },

  checkOverlap: (startDate: string, endDate: string, excludeId?: string) =>
    apiGet<{ has_overlap: boolean }>('/vacations/check-overlap', {
      params: { start_date: startDate, end_date: endDate, exclude_id: excludeId },
    }).then((r) => ({ hasOverlap: r.has_overlap })),
};

export const approvalsApi = {
  listVacations: async (params?: { offset?: number; limit?: number }) => {
    const res = await apiGet<OffsetList<BackendVacationRequest>>('/approvals/vacations', {
      params: { offset: params?.offset ?? 0, limit: params?.limit ?? 20 },
    });
    return { ...res, items: res.items.map(mapVacationRequest) };
  },

  approve: async (id: string, comment?: string) => {
    const raw = await apiPost<BackendVacationRequest>(
      `/approvals/vacations/${id}/approve`,
      { comment: comment ?? null }
    );
    return mapVacationRequest(raw);
  },

  reject: async (id: string, comment: string) => {
    const raw = await apiPost<BackendVacationRequest>(
      `/approvals/vacations/${id}/reject`,
      { comment }
    );
    return mapVacationRequest(raw);
  },
};
