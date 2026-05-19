'use client';

import { useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { ChevronLeft, FileUp, Loader2, Save, Thermometer } from 'lucide-react';
import { sickLeavesApi } from '@/lib/api/sickLeaves';
import { Badge } from '@/components/ui/Badge';
import { PageLoader } from '@/components/ui/LoadingSpinner';
import { SickLeaveStatus } from '@corp-portal/shared-types';
import { formatDateRangeRu, formatDateRu } from '@corp-portal/ui-core';

const closeSchema = z.object({
  endDate: z.string().min(1, 'Укажите дату окончания'),
  comment: z.string().optional(),
});

type CloseForm = z.infer<typeof closeSchema>;

export default function SickLeaveDetailPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const id = searchParams.get('id') ?? '';
  const queryClient = useQueryClient();
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);

  const { data: sickLeave, isLoading } = useQuery({
    queryKey: ['sick-leave', id],
    queryFn: () => sickLeavesApi.getById(id),
    enabled: Boolean(id),
  });

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
    setError,
  } = useForm<CloseForm>({
    resolver: zodResolver(closeSchema),
    values: {
      endDate: sickLeave?.endDate ?? new Date().toISOString().split('T')[0],
      comment: '',
    },
  });

  if (!id) {
    return <p className="text-sm text-gray-500">Больничный не выбран</p>;
  }

  if (isLoading || !sickLeave) return <PageLoader />;

  const refresh = async () => {
    await queryClient.invalidateQueries({ queryKey: ['sick-leave', id] });
    await queryClient.invalidateQueries({ queryKey: ['sick-leaves'] });
  };

  const onClose = async (data: CloseForm) => {
    try {
      await sickLeavesApi.close(id, {
        endDate: data.endDate,
        comment: data.comment || undefined,
      });
      await refresh();
    } catch (err) {
      setError('root', { message: err instanceof Error ? err.message : 'Не удалось закрыть больничный' });
    }
  };

  const onUpload = async () => {
    if (!file) return;
    setUploading(true);
    try {
      await sickLeavesApi.uploadDocument(id, file);
      setFile(null);
      await refresh();
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto space-y-5">
      <div className="flex items-center gap-3">
        <button
          onClick={() => router.back()}
          className="w-8 h-8 flex items-center justify-center rounded-xl hover:bg-gray-100 transition-colors"
        >
          <ChevronLeft className="w-5 h-5 text-gray-600" />
        </button>
        <div>
          <h1 className="text-xl font-bold text-gray-900">Больничный</h1>
          <p className="text-sm text-gray-500">
            {sickLeave.endDate
              ? formatDateRangeRu(sickLeave.startDate, sickLeave.endDate)
              : `С ${formatDateRu(sickLeave.startDate)}`}
          </p>
        </div>
      </div>

      <section className="bg-white rounded-2xl shadow-card p-5 space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-warning-100 flex items-center justify-center">
              <Thermometer className="w-5 h-5 text-warning-600" />
            </div>
            <div>
              <p className="text-sm font-semibold text-gray-900">Статус</p>
              <Badge status={sickLeave.status} />
            </div>
          </div>
          {sickLeave.calendarDays && (
            <p className="text-sm text-gray-500">{sickLeave.calendarDays} календарных дн.</p>
          )}
        </div>

        {sickLeave.comment && (
          <p className="text-sm text-gray-600 bg-gray-50 rounded-xl px-4 py-3">{sickLeave.comment}</p>
        )}

        {sickLeave.documentUrl ? (
          <a
            href={sickLeave.documentUrl}
            target="_blank"
            rel="noreferrer"
            className="inline-flex items-center gap-2 text-sm text-accent-700 hover:text-accent-900"
          >
            <FileUp className="w-4 h-4" />
            Открыть документ
          </a>
        ) : (
          <div className="space-y-3">
            <label className="block text-sm font-medium text-gray-700">Прикрепить документ</label>
            <input
              type="file"
              accept=".pdf,.jpg,.jpeg,.png"
              onChange={(event) => setFile(event.target.files?.[0] ?? null)}
              className="block w-full text-sm text-gray-600"
            />
            <button
              type="button"
              onClick={onUpload}
              disabled={!file || uploading}
              className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-warning-600 text-white text-sm font-medium hover:bg-warning-700 disabled:opacity-60"
            >
              {uploading ? <Loader2 className="w-4 h-4 animate-spin" /> : <FileUp className="w-4 h-4" />}
              Загрузить
            </button>
          </div>
        )}
      </section>

      {sickLeave.status === SickLeaveStatus.Open && (
        <section className="bg-white rounded-2xl shadow-card p-5">
          <h2 className="text-sm font-semibold text-gray-900 mb-4">Закрыть больничный</h2>
          <form onSubmit={handleSubmit(onClose)} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">Дата окончания</label>
              <input
                {...register('endDate')}
                type="date"
                className="w-full px-3.5 py-2.5 rounded-xl border border-gray-300 text-sm outline-none focus:ring-2 focus:ring-accent-500"
              />
              {errors.endDate && <p className="mt-1 text-xs text-danger-600">{errors.endDate.message}</p>}
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">Комментарий</label>
              <textarea
                {...register('comment')}
                rows={3}
                className="w-full px-3.5 py-2.5 rounded-xl border border-gray-300 text-sm outline-none focus:ring-2 focus:ring-accent-500 resize-none"
              />
            </div>
            {errors.root && <p className="text-sm text-danger-600">{errors.root.message}</p>}
            <button
              type="submit"
              disabled={isSubmitting}
              className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-primary-800 text-white text-sm font-medium hover:bg-primary-900 disabled:opacity-60"
            >
              {isSubmitting ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
              Закрыть
            </button>
          </form>
        </section>
      )}
    </div>
  );
}
