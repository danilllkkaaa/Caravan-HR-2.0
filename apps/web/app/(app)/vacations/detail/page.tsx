'use client';

import { useRouter, useSearchParams } from 'next/navigation';
import { ChevronLeft, Calendar, Clock, MessageSquare, XCircle } from 'lucide-react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { vacationsApi } from '@/lib/api/vacations';
import { useVacation } from '@/lib/hooks/useVacations';
import { Badge } from '@/components/ui/Badge';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { formatDateRangeRu, formatRelativeDate } from '@corp-portal/ui-core';

const Box = 'section' as const;

function DetailRow({
  icon: Icon,
  label,
  value,
}: {
  icon: React.ComponentType<{ className?: string }>;
  label: string;
  value: string;
}) {
  return (
    <Box className="flex items-start gap-3 px-5 py-4">
      <Icon className="w-4 h-4 text-gray-400 mt-0.5" />
      <Box>
        <p className="text-xs text-gray-500">{label}</p>
        <p className="text-sm font-semibold text-gray-900 mt-0.5">{value}</p>
      </Box>
    </Box>
  );
}

export default function VacationDetailPage() {
  const searchParams = useSearchParams();
  const id = searchParams.get('id') ?? undefined;
  const router = useRouter();
  const queryClient = useQueryClient();

  const { data: vacation, isLoading, isError } = useVacation(id);

  const cancelMutation = useMutation({
    mutationFn: () => vacationsApi.cancel(id!),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['vacation', id] });
      void queryClient.invalidateQueries({ queryKey: ['vacations'] });
      router.push('/vacations');
    },
  });

  if (isLoading) {
    return (
      <Box className="flex items-center justify-center min-h-[60vh]">
        <LoadingSpinner size="lg" />
      </Box>
    );
  }

  if (isError || !vacation) {
    return (
      <Box className="text-center py-16">
        <p className="text-gray-500">Заявка не найдена</p>
        <button
          type="button"
          onClick={() => router.back()}
          className="mt-4 text-sm text-accent-600 hover:underline"
        >
          Вернуться назад
        </button>
      </Box>
    );
  }

  const canCancel = vacation.status === 'pending';

  return (
    <Box className="max-w-lg mx-auto">
      <Box className="flex items-center gap-3 mb-6">
        <button
          type="button"
          onClick={() => router.back()}
          className="w-8 h-8 flex items-center justify-center rounded-xl hover:bg-gray-100 transition-colors"
        >
          <ChevronLeft className="w-5 h-5 text-gray-600" />
        </button>
        <Box>
          <h1 className="text-xl font-bold text-gray-900">{vacation.vacationType.name}</h1>
          <p className="text-sm text-gray-500">Заявка</p>
        </Box>
        <Box className="ml-auto">
          <Badge status={vacation.status} />
        </Box>
      </Box>

      <Box className="bg-white rounded-2xl shadow-card divide-y divide-gray-50 mb-4">
        <DetailRow
          icon={Calendar}
          label="Период"
          value={formatDateRangeRu(vacation.startDate, vacation.endDate)}
        />
        <DetailRow icon={Clock} label="Дней отпуска" value={String(vacation.daysCount)} />
        {vacation.comment && (
          <DetailRow icon={MessageSquare} label="Комментарий" value={vacation.comment} />
        )}
        {vacation.rejectionReason && (
          <Box className="flex items-start gap-3 px-5 py-4 bg-danger-50">
            <XCircle className="w-4 h-4 text-danger-500 mt-0.5" />
            <Box>
              <p className="text-xs text-danger-600 font-medium">Причина отказа</p>
              <p className="text-sm text-danger-700 mt-0.5">{vacation.rejectionReason}</p>
            </Box>
          </Box>
        )}
      </Box>

      <Box className="bg-white rounded-2xl shadow-card px-5 py-4 mb-4">
        <h2 className="text-sm font-semibold text-gray-700 mb-4">История</h2>
        <p className="text-xs text-gray-500">
          Создано: {formatRelativeDate(vacation.createdAt)}
        </p>
        {vacation.approvedAt && (
          <p className="text-xs text-gray-500 mt-1">
            Решение: {formatRelativeDate(vacation.approvedAt)}
          </p>
        )}
      </Box>

      {canCancel && (
        <button
          type="button"
          onClick={() => cancelMutation.mutate()}
          disabled={cancelMutation.isPending}
          className="w-full flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl border border-danger-200 text-danger-600 hover:bg-danger-50 text-sm font-medium transition-colors disabled:opacity-50"
        >
          {cancelMutation.isPending ? <LoadingSpinner size="sm" /> : <XCircle className="w-4 h-4" />}
          Отозвать заявку
        </button>
      )}
    </Box>
  );
}
