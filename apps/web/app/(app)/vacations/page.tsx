'use client';

import { useState } from 'react';
import Link from 'next/link';
import { Plus, Filter } from 'lucide-react';
import { useVacationsList } from '@/lib/hooks/useVacations';
import type { VacationRequestView } from '@/lib/types/views';
import { Badge } from '@/components/ui/Badge';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { formatDateRangeRu } from '@corp-portal/ui-core';
import clsx from 'clsx';

const Box = 'section' as const;

const STATUS_LABELS: Record<string, string> = {
  draft: 'Черновик',
  pending: 'На рассмотрении',
  approved: 'Утверждён',
  rejected: 'Отклонён',
  cancelled: 'Отменён',
};

const FILTER_OPTIONS: Array<{ value: string; label: string }> = [
  { value: 'all', label: 'Все' },
  { value: 'pending', label: 'На рассмотрении' },
  { value: 'approved', label: 'Утверждённые' },
  { value: 'rejected', label: 'Отклонённые' },
  { value: 'cancelled', label: 'Отменённые' },
];

function VacationCard({ vacation }: { vacation: VacationRequestView }) {
  return (
    <Link
      href={`/vacations/detail?id=${vacation.id}`}
      className="block bg-white rounded-2xl shadow-card hover:shadow-card-hover transition-shadow p-5"
    >
      <Box className="flex items-start justify-between gap-3">
        <Box className="flex-1 min-w-0">
          <Box className="flex items-center gap-2 mb-1">
            <span className="text-sm font-semibold text-gray-900">
              {vacation.vacationType.name}
            </span>
            <Badge status={vacation.status} label={STATUS_LABELS[vacation.status]} />
          </Box>
          <p className="text-sm text-gray-600">
            {formatDateRangeRu(vacation.startDate, vacation.endDate)}
          </p>
          <p className="text-xs text-gray-400 mt-1">{vacation.daysCount} дн.</p>
        </Box>
        <Box className="text-right flex-shrink-0">
          <p className="text-lg font-bold text-gray-900">{vacation.daysCount}</p>
          <p className="text-xs text-gray-400">дн.</p>
        </Box>
      </Box>
      {vacation.comment && (
        <p className="mt-3 pt-3 border-t border-gray-50 text-xs text-gray-500 line-clamp-2">
          {vacation.comment}
        </p>
      )}
      {vacation.rejectionReason && (
        <p className="mt-3 pt-3 border-t border-danger-50 text-xs text-danger-600 line-clamp-2">
          Причина отказа: {vacation.rejectionReason}
        </p>
      )}
    </Link>
  );
}

function VacationsFilters({
  yearOptions,
  yearFilter,
  setYearFilter,
  statusFilter,
  setStatusFilter,
}: {
  yearOptions: number[];
  yearFilter: number;
  setYearFilter: (y: number) => void;
  statusFilter: string;
  setStatusFilter: (s: string) => void;
}) {
  return (
    <Box className="space-y-3">
      <Box className="flex items-center gap-2">
        <span className="text-xs text-gray-500 font-medium">Год:</span>
        {yearOptions.map((y) => (
          <button
            key={y}
            type="button"
            onClick={() => setYearFilter(y)}
            className={clsx(
              'px-3 py-1.5 rounded-lg text-xs font-medium transition-colors',
              yearFilter === y
                ? 'bg-primary-800 text-white'
                : 'bg-white text-gray-600 border border-gray-200 hover:bg-gray-50'
            )}
          >
            {y}
          </button>
        ))}
      </Box>
      <Box className="flex flex-wrap items-center gap-2">
        <Filter className="w-3.5 h-3.5 text-gray-400" />
        {FILTER_OPTIONS.map((opt) => (
          <button
            key={opt.value}
            type="button"
            onClick={() => setStatusFilter(opt.value)}
            className={clsx(
              'px-3 py-1.5 rounded-lg text-xs font-medium transition-colors',
              statusFilter === opt.value
                ? 'bg-primary-800 text-white'
                : 'bg-white text-gray-600 border border-gray-200 hover:bg-gray-50'
            )}
          >
            {opt.label}
          </button>
        ))}
      </Box>
    </Box>
  );
}

export default function VacationsPage() {
  const currentYear = new Date().getFullYear();
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [yearFilter, setYearFilter] = useState<number>(currentYear);

  const { data, isLoading, isError } = useVacationsList({
    status: statusFilter === 'all' ? undefined : statusFilter,
    year: yearFilter,
  });

  const allItems = data?.items ?? [];

  const groupedByYear = allItems.reduce<Record<number, VacationRequestView[]>>((acc, v) => {
    const y = new Date(v.startDate).getFullYear();
    if (!acc[y]) acc[y] = [];
    acc[y].push(v);
    return acc;
  }, {});

  const sortedYears = Object.keys(groupedByYear)
    .map(Number)
    .sort((a, b) => b - a);

  const yearOptions = Array.from({ length: 4 }, (_, i) => currentYear - i);

  return (
    <Box className="space-y-5">
      <Box className="flex items-center justify-between">
        <Box>
          <h1 className="text-2xl font-bold text-gray-900">Мои отпуска</h1>
          <p className="text-gray-500 text-sm mt-0.5">История заявок на отпуск</p>
        </Box>
        <Link
          href="/vacations/new"
          className="flex items-center gap-2 px-4 py-2 bg-primary-800 text-white rounded-xl text-sm font-medium hover:bg-primary-900 transition-colors"
        >
          <Plus className="w-4 h-4" />
          <span className="hidden sm:inline">Новый отпуск</span>
        </Link>
      </Box>

      <VacationsFilters
        yearOptions={yearOptions}
        yearFilter={yearFilter}
        setYearFilter={setYearFilter}
        statusFilter={statusFilter}
        setStatusFilter={setStatusFilter}
      />

      {isLoading ? (
        <Box className="flex justify-center py-12">
          <LoadingSpinner size="lg" />
        </Box>
      ) : isError ? (
        <Box className="text-center py-12">
          <p className="text-gray-500">Не удалось загрузить данные</p>
        </Box>
      ) : allItems.length === 0 ? (
        <Box className="text-center py-16">
          <p className="text-gray-700 font-medium">Заявок не найдено</p>
          <p className="text-gray-400 text-sm mt-1">
            <Link href="/vacations/new" className="text-accent-600 hover:underline">
              Подайте новую заявку
            </Link>
          </p>
        </Box>
      ) : (
        <Box className="space-y-6">
          {sortedYears.map((year) => (
            <Box key={year}>
              <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-3">
                {year} год
              </h2>
              <Box className="space-y-3">
                {(groupedByYear[year] ?? []).map((v) => (
                  <VacationCard key={v.id} vacation={v} />
                ))}
              </Box>
            </Box>
          ))}
        </Box>
      )}
    </Box>
  );
}
