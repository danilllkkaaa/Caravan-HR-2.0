'use client';

import { useState } from 'react';
import { CheckCircle2, XCircle, Clock, Loader2, AlertCircle } from 'lucide-react';
import Image from 'next/image';
import { usePendingApprovals, useApproveVacation, useRejectVacation } from '@/lib/hooks/useApprovals';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { formatDateRangeRu, formatRelativeDate } from '@corp-portal/ui-core';
import type { VacationRequestView } from '@/lib/types/views';

function RejectModal({
  request,
  onClose,
  onConfirm,
  isLoading,
}: {
  request: VacationRequestView;
  onClose: () => void;
  onConfirm: (comment: string) => void;
  isLoading: boolean;
}) {
  const [reason, setReason] = useState('');
  const isValid = reason.trim().length >= 1;
  const empName = request.employee?.fullName ?? 'Сотрудник';

  return (
    <div className="fixed inset-0 z-50 flex items-end sm:items-center justify-center p-4 bg-black/40 backdrop-blur-sm">
      <div className="w-full max-w-md bg-white rounded-2xl shadow-xl">
        <div className="px-6 py-5 border-b border-gray-100">
          <h3 className="text-base font-semibold text-gray-900">Отклонить заявку</h3>
          <p className="text-sm text-gray-500 mt-0.5">
            {empName} · {formatDateRangeRu(request.startDate, request.endDate)}
          </p>
        </div>
        <div className="px-6 py-5">
          <label className="block text-sm font-medium text-gray-700 mb-1.5">
            Причина отклонения <span className="text-danger-500">*</span>
          </label>
          <textarea
            value={reason}
            onChange={(e) => setReason(e.target.value)}
            rows={3}
            placeholder="Укажите причину отклонения заявки…"
            className="w-full px-3.5 py-2.5 rounded-xl border border-gray-300 text-sm resize-none outline-none focus:ring-2 focus:ring-danger-500 focus:border-danger-500 transition-colors"
            autoFocus
          />
          {reason.trim().length === 0 && (
            <p className="mt-1.5 text-xs text-danger-600">Комментарий обязателен</p>
          )}
        </div>
        <div className="px-6 pb-5 flex items-center gap-3">
          <button
            type="button"
            onClick={onClose}
            disabled={isLoading}
            className="flex-1 py-2.5 rounded-xl border border-gray-200 text-sm font-medium text-gray-700 hover:bg-gray-50 transition-colors disabled:opacity-50"
          >
            Отмена
          </button>
          <button
            type="button"
            onClick={() => onConfirm(reason.trim())}
            disabled={!isValid || isLoading}
            className="flex-1 flex items-center justify-center gap-2 py-2.5 rounded-xl bg-danger-600 text-white text-sm font-medium hover:bg-danger-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <XCircle className="w-4 h-4" />}
            Отклонить
          </button>
        </div>
      </div>
    </div>
  );
}

function ApprovalCard({
  request,
  onApprove,
  onReject,
  isApproving,
}: {
  request: VacationRequestView;
  onApprove: () => void;
  onReject: () => void;
  isApproving: boolean;
}) {
  const emp = request.employee;
  const name = emp?.fullName ?? 'Сотрудник';
  const initials = emp
    ? `${emp.firstName[0] ?? ''}${emp.lastName[0] ?? ''}`
    : '?';

  return (
    <div className="bg-white rounded-2xl shadow-card p-5">
      <div className="flex items-start gap-3 mb-4">
        <div className="w-10 h-10 rounded-full bg-primary-100 flex items-center justify-center flex-shrink-0 overflow-hidden">
          {emp?.avatarUrl ? (
            <Image src={emp.avatarUrl} alt={name} width={40} height={40} className="w-10 h-10 rounded-full object-cover" />
          ) : (
            <span className="text-sm font-bold text-primary-700">{initials}</span>
          )}
        </div>
        <div className="flex-1 min-w-0">
          <p className="text-sm font-semibold text-gray-900">{name}</p>
          {emp?.personnelNumber && (
            <p className="text-xs text-gray-500">Таб. № {emp.personnelNumber}</p>
          )}
        </div>
        <span className="text-xs text-gray-400 flex-shrink-0">{formatRelativeDate(request.createdAt)}</span>
      </div>

      <div className="bg-gray-50 rounded-xl px-4 py-3 mb-4 space-y-1">
        <div className="flex items-center justify-between">
          <span className="text-xs font-medium text-gray-500">Тип отпуска</span>
          <span className="text-xs font-semibold text-gray-900">{request.vacationType.name}</span>
        </div>
        <div className="flex items-center justify-between">
          <span className="text-xs font-medium text-gray-500">Период</span>
          <span className="text-xs font-semibold text-gray-900">
            {formatDateRangeRu(request.startDate, request.endDate)}
          </span>
        </div>
        <div className="flex items-center justify-between">
          <span className="text-xs font-medium text-gray-500">Дней</span>
          <span className="text-xs font-semibold text-gray-900">{request.daysCount}</span>
        </div>
      </div>

      {request.comment && (
        <div className="flex items-start gap-2 mb-4 px-1">
          <AlertCircle className="w-3.5 h-3.5 text-gray-400 mt-0.5 flex-shrink-0" />
          <p className="text-xs text-gray-500 italic">{request.comment}</p>
        </div>
      )}

      <div className="flex items-center gap-3">
        <button
          type="button"
          onClick={onReject}
          disabled={isApproving}
          className="flex-1 flex items-center justify-center gap-2 py-2.5 rounded-xl border border-danger-200 text-sm font-medium text-danger-600 hover:bg-danger-50 transition-colors disabled:opacity-50"
        >
          <XCircle className="w-4 h-4" />
          Отклонить
        </button>
        <button
          type="button"
          onClick={onApprove}
          disabled={isApproving}
          className="flex-1 flex items-center justify-center gap-2 py-2.5 rounded-xl bg-success-600 text-white text-sm font-medium hover:bg-success-700 transition-colors disabled:opacity-50"
        >
          {isApproving ? <Loader2 className="w-4 h-4 animate-spin" /> : <CheckCircle2 className="w-4 h-4" />}
          Согласовать
        </button>
      </div>
    </div>
  );
}

export default function ApprovalsPage() {
  const { data, isLoading, isError } = usePendingApprovals();
  const approveMutation = useApproveVacation();
  const rejectMutation = useRejectVacation();

  const [rejectTarget, setRejectTarget] = useState<VacationRequestView | null>(null);
  const [approvingId, setApprovingId] = useState<string | null>(null);

  const allItems = data?.items ?? [];

  const handleApprove = async (request: VacationRequestView) => {
    setApprovingId(request.id);
    try {
      await approveMutation.mutateAsync({ id: request.id });
    } finally {
      setApprovingId(null);
    }
  };

  const handleRejectConfirm = async (comment: string) => {
    if (!rejectTarget) return;
    await rejectMutation.mutateAsync({ id: rejectTarget.id, comment });
    setRejectTarget(null);
  };

  return (
    <>
      <div className="space-y-5">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Согласование</h1>
          <p className="text-gray-500 text-sm mt-0.5">
            Заявки ваших подчинённых, ожидающие решения
          </p>
        </div>

        {!isLoading && allItems.length > 0 && (
          <div className="flex items-center gap-2 px-4 py-3 bg-warning-50 border border-warning-200 rounded-xl">
            <Clock className="w-4 h-4 text-warning-600 flex-shrink-0" />
            <p className="text-sm text-warning-700">
              <span className="font-semibold">{allItems.length}</span> заявок ожидают вашего решения
            </p>
          </div>
        )}

        {isLoading ? (
          <div className="flex justify-center py-16">
            <LoadingSpinner size="lg" />
          </div>
        ) : isError ? (
          <div className="text-center py-16">
            <p className="text-gray-500">Не удалось загрузить заявки</p>
          </div>
        ) : allItems.length === 0 ? (
          <div className="text-center py-20">
            <div className="w-16 h-16 rounded-full bg-success-50 flex items-center justify-center mx-auto mb-4">
              <CheckCircle2 className="w-8 h-8 text-success-500" />
            </div>
            <p className="text-gray-700 font-semibold text-lg">Все заявки обработаны</p>
            <p className="text-gray-400 text-sm mt-1">Новые заявки появятся здесь автоматически</p>
          </div>
        ) : (
          <div className="space-y-4">
            {allItems.map((request) => (
              <ApprovalCard
                key={request.id}
                request={request}
                onApprove={() => void handleApprove(request)}
                onReject={() => setRejectTarget(request)}
                isApproving={approvingId === request.id}
              />
            ))}
          </div>
        )}
      </div>

      {rejectTarget && (
        <RejectModal
          request={rejectTarget}
          onClose={() => setRejectTarget(null)}
          onConfirm={(reason) => void handleRejectConfirm(reason)}
          isLoading={rejectMutation.isPending}
        />
      )}
    </>
  );
}
