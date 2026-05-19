import { useQuery } from '@tanstack/react-query';
import { vacationsApi } from '@/lib/api/vacations';
import { useAuthStore } from '@corp-portal/ui-core';

interface UseVacationsListParams {
  status?: string;
  year?: number;
  limit?: number;
}

export function useVacationsList(params?: UseVacationsListParams) {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);

  return useQuery({
    queryKey: ['vacations', params],
    queryFn: () =>
      vacationsApi.list({
        status: params?.status,
        year: params?.year,
        limit: params?.limit ?? 50,
      }),
    enabled: isAuthenticated,
    staleTime: 30 * 1000,
  });
}

export function useVacationTypes() {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);

  return useQuery({
    queryKey: ['vacation-types'],
    queryFn: vacationsApi.getTypes,
    enabled: isAuthenticated,
    staleTime: 10 * 60 * 1000,
  });
}

export function useVacationBalance(year?: number) {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  const currentYear = new Date().getFullYear();

  return useQuery({
    queryKey: ['vacation-balance', year ?? currentYear],
    queryFn: () => vacationsApi.getBalance(year ?? currentYear),
    enabled: isAuthenticated,
    staleTime: 5 * 60 * 1000,
  });
}

export function useVacation(id: string | undefined) {
  return useQuery({
    queryKey: ['vacation', id],
    queryFn: () => vacationsApi.getById(id!),
    enabled: Boolean(id),
  });
}
