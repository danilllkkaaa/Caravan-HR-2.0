'use client';

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useRouter } from 'next/navigation';
import { ChevronLeft, MonitorSmartphone, Trash2 } from 'lucide-react';
import { authApi } from '@/lib/api/auth';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { formatRelativeDate } from '@corp-portal/ui-core';
import type { UserSession } from '@corp-portal/shared-types';

function deviceLabel(session: UserSession) {
  const deviceInfo = session.deviceInfo as unknown as Record<string, unknown> | undefined;
  const ua = typeof deviceInfo?.user_agent === 'string' ? deviceInfo.user_agent : '';
  if (ua.includes('Mobile')) return 'Мобильное устройство';
  if (ua) return 'Браузер';
  return 'Устройство';
}

export default function SessionsPage() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const { data, isLoading, isError } = useQuery({
    queryKey: ['auth', 'sessions'],
    queryFn: authApi.getSessions,
  });

  const revokeMutation = useMutation({
    mutationFn: authApi.revokeSession,
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['auth', 'sessions'] });
    },
  });

  return (
    <div className="max-w-lg mx-auto space-y-5">
      <div className="flex items-center gap-3">
        <button
          type="button"
          onClick={() => router.back()}
          className="w-8 h-8 flex items-center justify-center rounded-xl hover:bg-gray-100 transition-colors"
        >
          <ChevronLeft className="w-5 h-5 text-gray-600" />
        </button>
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Мои устройства</h1>
          <p className="text-sm text-gray-500">Активные сессии аккаунта</p>
        </div>
      </div>

      {isLoading ? (
        <div className="flex justify-center py-12">
          <LoadingSpinner size="lg" />
        </div>
      ) : isError ? (
        <div className="text-center py-12 text-sm text-gray-500">
          Не удалось загрузить список сессий
        </div>
      ) : !data || data.length === 0 ? (
        <div className="text-center py-12 text-sm text-gray-500">
          Активных сессий не найдено
        </div>
      ) : (
        <div className="bg-white rounded-2xl shadow-card divide-y divide-gray-50 overflow-hidden">
          {data.map((session) => (
            <div key={String(session.id)} className="flex items-center gap-3 px-5 py-4">
              <div className="w-10 h-10 rounded-xl bg-gray-100 flex items-center justify-center flex-shrink-0">
                <MonitorSmartphone className="w-5 h-5 text-gray-500" />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-semibold text-gray-900">{deviceLabel(session)}</p>
                <p className="text-xs text-gray-500 mt-0.5">
                  Создана {formatRelativeDate(session.createdAt)}
                </p>
                <p className="text-xs text-gray-400 mt-0.5 truncate">
                  IP: {
                    typeof (session.deviceInfo as unknown as Record<string, unknown>)?.ip === 'string'
                      ? String((session.deviceInfo as unknown as Record<string, unknown>).ip)
                      : 'unknown'
                  }
                </p>
              </div>
              <button
                type="button"
                onClick={() => revokeMutation.mutate(session.id)}
                disabled={revokeMutation.isPending}
                className="w-9 h-9 flex items-center justify-center rounded-xl text-danger-600 hover:bg-danger-50 transition-colors disabled:opacity-50"
              >
                <Trash2 className="w-4 h-4" />
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
