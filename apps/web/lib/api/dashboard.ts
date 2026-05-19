import { apiGet } from './client';
import { mapDashboard, type BackendDashboard } from './mappers';
import type { DashboardView } from '@/lib/types/views';

export const dashboardApi = {
  get: async (): Promise<DashboardView> => {
    const raw = await apiGet<BackendDashboard>('/dashboard');
    return mapDashboard(raw);
  },
};
