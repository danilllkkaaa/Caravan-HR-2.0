'use client';

import { useQuery } from '@tanstack/react-query';
import { employeesApi } from '@/lib/api/employees';

interface UseEmployeesParams {
  search?: string;
  departmentId?: string;
  page?: number;
  pageSize?: number;
  isActive?: boolean;
}

export function useEmployees(params: UseEmployeesParams = {}) {
  return useQuery({
    queryKey: ['employees', params],
    queryFn: () => employeesApi.list(params),
    staleTime: 2 * 60_000,
    placeholderData: (prev) => prev,
  });
}

export function useEmployee(id: string | null) {
  return useQuery({
    queryKey: ['employees', id],
    queryFn: () => employeesApi.getById(id!),
    enabled: id !== null,
    staleTime: 5 * 60_000,
  });
}

export function useMyEmployee(enabled = true) {
  return useQuery({
    queryKey: ['employees', 'me'],
    queryFn: employeesApi.getMe,
    enabled,
    staleTime: 5 * 60_000,
  });
}

export function useDepartments() {
  return useQuery({
    queryKey: ['departments'],
    queryFn: () => employeesApi.getDepartments(),
    staleTime: 30 * 60_000,
  });
}
