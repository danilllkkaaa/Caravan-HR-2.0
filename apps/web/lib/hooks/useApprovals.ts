'use client';

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { approvalsApi } from '@/lib/api/vacations';
import { useAuthStore } from '@corp-portal/ui-core';

export function usePendingApprovals() {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);

  return useQuery({
    queryKey: ['approvals', 'vacations'],
    queryFn: () => approvalsApi.listVacations({ limit: 50 }),
    enabled: isAuthenticated,
    staleTime: 30 * 1000,
    refetchInterval: 30 * 1000,
  });
}

export function useApproveVacation() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, comment }: { id: string; comment?: string }) =>
      approvalsApi.approve(id, comment),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ['approvals'] });
      void qc.invalidateQueries({ queryKey: ['vacations'] });
      void qc.invalidateQueries({ queryKey: ['notifications'] });
    },
  });
}

export function useRejectVacation() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, comment }: { id: string; comment: string }) =>
      approvalsApi.reject(id, comment),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ['approvals'] });
      void qc.invalidateQueries({ queryKey: ['vacations'] });
      void qc.invalidateQueries({ queryKey: ['notifications'] });
    },
  });
}
