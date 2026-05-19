'use client';

import { useState } from 'react';
import Link from 'next/link';
import { Plus, Thermometer } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { sickLeavesApi } from '@/lib/api/sickLeaves';
import { SickLeaveStatus } from '@corp-portal/shared-types';
import type { SickLeave } from '@corp-portal/shared-types';
import { Badge } from '@/components/ui/Badge';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { formatDateRu, formatDateRangeRu } from '@corp-portal/ui-core';
import clsx from 'clsx';

const FILTER_OPTIONS: Array<{ value: SickLeaveStatus | 'all'; label: string }> = [
  { value: 'all', label: 'Все' },
  { value: SickLeaveStatus.Open, label: 'Открытые' },
  { value: SickLeaveStatus.Closed, label: 'Закрытые' },
];

function SickLeaveCard({ sickLeave }: { sickLeave: SickLeave }) {
  return (
    <Link href={`/sick-leaves/detail?id=${sickLeave.id}`} className="block bg-white rounded-2xl shadow-card p-5 hover:shadow-md transition-shadow">
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-1.5">
            <div className="w-8 h-8 rounded-full bg-warning-100 flex items-center justify-center">
              <Thermometer className="w-4 h-4 text-warning-600" />
            </div>
            <Badge status={sickLeave.status} />
          </div>
          <p className="text-sm font-semibold text-gray-900">
            {sickLeave.endDate
              ? formatDateRangeRu(sickLeave.startDate, sickLeave.endDate)
              : `С ${formatDateRu(sickLeave.startDate)} — открыт`}
          </p>
          {sickLeave.calendarDays && (
            <p className="text-xs text-gray-500 mt-0.5">
              {sickLeave.calendarDays} календарных дн.
              {sickLeave.workingDays != null && ` · ${sickLeave.workingDays} рабочих`}
            </p>
          )}
        </div>
        {sickLeave.status === SickLeaveStatus.Open && (
          <span className="flex items-center gap-1 text-xs font-medium text-warning-600 bg-warning-50 px-2.5 py-1 rounded-full">
            <span className="w-1.5 h-1.5 rounded-full bg-warning-500 animate-pulse" />
            Активен
          </span>
        )}
      </div>

      {sickLeave.documentNumber && (
        <div className="mt-3 pt-3 border-t border-gray-50">
          <p className="text-xs text-gray-500">
            Листок нетрудоспособности: <span className="font-medium text-gray-700">{sickLeave.documentNumber}</span>
          </p>
        </div>
      )}

      {sickLeave.comment && (
        <p className="mt-2 text-xs text-gray-400 italic line-clamp-2">{sickLeave.comment}</p>
      )}
    </Link>
  );
}

export default function SickLeavesPage() {
  const [statusFilter, setStatusFilter] = useState<SickLeaveStatus | 'all'>('all');

  const { data, isLoading, isError } = useQuery({
    queryKey: ['sick-leaves', statusFilter],
    queryFn: () =>
      sickLeavesApi.list({
        status: statusFilter === 'all' ? undefined : statusFilter,
      }),
  });

  const items = data?.items ?? [];
  const hasOpenLeave = items.some((s) => s.status === SickLeaveStatus.Open);

  return (
    <div className="space-y-5">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Больничные</h1>
          <p className="text-gray-500 text-sm mt-0.5">История больничных листов</p>
        </div>
        {!hasOpenLeave && (
          <Link
            href="/sick-leaves/new"
            className="flex items-center gap-2 px-4 py-2 bg-primary-800 text-white rounded-xl text-sm font-medium hover:bg-primary-900 transition-colors"
          >
            <Plus className="w-4 h-4" />
            <span className="hidden sm:inline">Открыть больничный</span>
          </Link>
        )}
      </div>

      {/* Active leave warning */}
      {hasOpenLeave && (
        <div className="bg-warning-50 border border-warning-200 rounded-2xl px-5 py-4 flex items-start gap-3">
          <Thermometer className="w-5 h-5 text-warning-600 flex-shrink-0 mt-0.5" />
          <div>
            <p className="text-sm font-semibold text-warning-800">У вас открытый больничный</p>
            <p className="text-xs text-warning-600 mt-0.5">
              Новый больничный можно открыть только после закрытия текущего.
            </p>
          </div>
        </div>
      )}

      {/* Status filter */}
      <div className="flex flex-wrap gap-2">
        {FILTER_OPTIONS.map((opt) => (
          <button
            key={opt.value}
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
      </div>

      {/* Content */}
      {isLoading ? (
        <div className="flex justify-center py-12">
          <LoadingSpinner size="lg" />
        </div>
      ) : isError ? (
        <div className="text-center py-12">
          <p className="text-gray-500">Не удалось загрузить данные</p>
        </div>
      ) : items.length === 0 ? (
        <div className="text-center py-16">
          <div className="w-14 h-14 rounded-full bg-gray-100 flex items-center justify-center mx-auto mb-4">
            <Thermometer className="w-7 h-7 text-gray-400" />
          </div>
          <p className="text-gray-700 font-medium">Больничных не найдено</p>
          <p className="text-gray-400 text-sm mt-1">Ничего не найдено по выбранным фильтрам</p>
        </div>
      ) : (
        <div className="space-y-3">
          {items.map((sl) => (
            <SickLeaveCard key={sl.id} sickLeave={sl} />
          ))}
        </div>
      )}
    </div>
  );
}
