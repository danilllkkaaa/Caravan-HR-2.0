'use client';

import { useState } from 'react';
import { ClipboardList, Loader2, X } from 'lucide-react';
import { useChangeRequests, useCancelChangeRequest } from '@/lib/hooks/usePersonalData';
import { Badge } from '@/components/ui/Badge';
import { PageLoader } from '@/components/ui/LoadingSpinner';
import { ChangeRequestStatus, ChangeRequestSection } from '@corp-portal/shared-types';

const STATUS_LABELS: Record<ChangeRequestStatus, string> = {
  [ChangeRequestStatus.Sent]: 'Отправлена',
  [ChangeRequestStatus.UnderReview]: 'На рассмотрении',
  [ChangeRequestStatus.Approved]: 'Одобрена',
  [ChangeRequestStatus.Rejected]: 'Отклонена',
};

const SECTION_LABELS: Record<ChangeRequestSection, string> = {
  [ChangeRequestSection.BasicData]: 'Основные данные',
  [ChangeRequestSection.Citizenship]: 'Гражданство',
  [ChangeRequestSection.Document]: 'Удостоверение',
  [ChangeRequestSection.Address]: 'Адрес',
  [ChangeRequestSection.Contacts]: 'Контакты',
  [ChangeRequestSection.Education]: 'Образование',
  [ChangeRequestSection.Family]: 'Семья',
  [ChangeRequestSection.EmergencyContact]: 'Экстренный контакт',
  [ChangeRequestSection.SocialInfo]: 'Социальные сведения',
  [ChangeRequestSection.Medical]: 'Медицинские справки',
  [ChangeRequestSection.Bank]: 'Банковские реквизиты',
};

const STATUS_FILTER_OPTIONS: Array<{ value: ChangeRequestStatus | 'all'; label: string }> = [
  { value: 'all', label: 'Все' },
  { value: ChangeRequestStatus.Sent, label: 'Отправлена' },
  { value: ChangeRequestStatus.UnderReview, label: 'На рассмотрении' },
  { value: ChangeRequestStatus.Approved, label: 'Одобрена' },
  { value: ChangeRequestStatus.Rejected, label: 'Отклонена' },
];

export default function ChangeRequestsPage() {
  const { data: requests, isLoading } = useChangeRequests();
  const { mutateAsync: cancel, isPending: cancelling } = useCancelChangeRequest();

  const [filter, setFilter] = useState<ChangeRequestStatus | 'all'>('all');
  const [cancellingId, setCancellingId] = useState<string | null>(null);

  const filtered =
    filter === 'all' ? (requests ?? []) : (requests ?? []).filter((r) => r.status === filter);

  const handleCancel = async (id: string) => {
    setCancellingId(id);
    try {
      await cancel(id);
    } finally {
      setCancellingId(null);
    }
  };

  if (isLoading) return <PageLoader />;

  return (
    <div className="space-y-4">
      <h2 className="text-base font-semibold text-gray-900">Мои заявки на изменение</h2>

      {/* Filter pills */}
      <div className="flex flex-wrap gap-2">
        {STATUS_FILTER_OPTIONS.map((opt) => (
          <button
            key={opt.value}
            onClick={() => setFilter(opt.value)}
            className={`px-3 py-1.5 rounded-full text-xs font-medium transition-colors ${
              filter === opt.value
                ? 'bg-primary-800 text-white'
                : 'bg-white border border-gray-200 text-gray-600 hover:bg-gray-50'
            }`}
          >
            {opt.label}
          </button>
        ))}
      </div>

      {filtered.length === 0 && (
        <div className="bg-white rounded-2xl shadow-card p-8 text-center">
          <ClipboardList className="w-8 h-8 text-gray-300 mx-auto mb-3" />
          <p className="text-sm font-medium text-gray-900 mb-1">Заявки не найдены</p>
          <p className="text-xs text-gray-400">
            {filter === 'all'
              ? 'У вас ещё нет заявок на изменение данных'
              : 'Нет заявок с выбранным статусом'}
          </p>
        </div>
      )}

      <div className="space-y-3">
        {filtered.map((req) => (
          <div key={req.id} className="bg-white rounded-2xl shadow-card p-4">
            <div className="flex items-start justify-between gap-3">
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 flex-wrap mb-1">
                  <span className="text-xs text-gray-500 bg-gray-100 px-2 py-0.5 rounded-full">
                    {SECTION_LABELS[req.section]}
                  </span>
                  <Badge
                    status={req.status}
                    label={STATUS_LABELS[req.status]}
                    dot
                  />
                </div>

                <p className="text-sm font-medium text-gray-900">{req.fieldName}</p>

                <div className="mt-2 space-y-1 text-xs text-gray-500">
                  <div className="flex gap-4">
                    <div>
                      <span className="text-gray-400">Было: </span>
                      <span className="text-gray-700">
                        {JSON.stringify(req.oldValue).replace(/[{}"]/g, '').replace(/:/g, ': ')}
                      </span>
                    </div>
                    <div>
                      <span className="text-gray-400">Стало: </span>
                      <span className="text-gray-700">
                        {JSON.stringify(req.newValue).replace(/[{}"]/g, '').replace(/:/g, ': ')}
                      </span>
                    </div>
                  </div>
                  {req.comment && (
                    <p>
                      <span className="text-gray-400">Комментарий: </span>
                      {req.comment}
                    </p>
                  )}
                  {req.status === ChangeRequestStatus.Rejected && req.hrComment && (
                    <div className="mt-2 bg-danger-50 border border-danger-200 rounded-xl px-3 py-2">
                      <p className="text-danger-700">
                        <span className="font-medium">Причина отклонения: </span>
                        {req.hrComment}
                      </p>
                    </div>
                  )}
                </div>

                <p className="text-xs text-gray-400 mt-2">
                  {new Date(req.createdAt).toLocaleDateString('ru-RU', {
                    day: '2-digit',
                    month: 'long',
                    year: 'numeric',
                    hour: '2-digit',
                    minute: '2-digit',
                  })}
                </p>
              </div>

              {req.status === ChangeRequestStatus.Sent && (
                <button
                  onClick={() => void handleCancel(req.id)}
                  disabled={cancellingId === req.id}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl border border-gray-200 text-xs font-medium text-gray-600 hover:bg-danger-50 hover:text-danger-700 hover:border-danger-200 transition-colors flex-shrink-0"
                >
                  {cancellingId === req.id ? (
                    <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  ) : (
                    <X className="w-3.5 h-3.5" />
                  )}
                  Отменить
                </button>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}


