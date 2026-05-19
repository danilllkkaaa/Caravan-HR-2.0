'use client';

import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Loader2, Save } from 'lucide-react';
import { useSocialInfo, useUpdateSocialInfo } from '@/lib/hooks/usePersonalData';
import { DataSourceBadge } from '@/components/personal-data/DataSourceBadge';
import { DocumentUpload } from '@/components/personal-data/DocumentUpload';
import { PageLoader } from '@/components/ui/LoadingSpinner';
import { getDocumentUploadUrl } from '@/lib/api/personalData';
import { ApiClientError } from '@/lib/api/client';

const schema = z.object({
  pensionStatus: z.string().optional(),
  hasDisability: z.boolean(),
  disabilityGroup: z.number().min(1).max(3).optional().nullable(),
  isWw2Veteran: z.boolean(),
  isWw2Family: z.boolean(),
});

type FormData = z.infer<typeof schema>;

export default function SocialPage() {
  const { data: info, isLoading } = useSocialInfo();
  const { mutateAsync: update, isPending } = useUpdateSocialInfo();

  const [documentKey, setDocumentKey] = useState<string | null>(null);
  const [serverError, setServerError] = useState<string | null>(null);
  const [saved, setSaved] = useState(false);

  const {
    register,
    handleSubmit,
    watch,
    formState: { errors, isDirty },
  } = useForm<FormData>({
    resolver: zodResolver(schema),
    values: {
      pensionStatus: info?.pensionStatus ?? '',
      hasDisability: info?.hasDisability ?? false,
      disabilityGroup: info?.disabilityGroup ?? null,
      isWw2Veteran: info?.isWw2Veteran ?? false,
      isWw2Family: info?.isWw2Family ?? false,
    },
  });

  const hasDisability = watch('hasDisability');

  const onSubmit = async (data: FormData) => {
    setServerError(null);
    try {
      await update({
        pensionStatus: data.pensionStatus ?? null,
        hasDisability: data.hasDisability,
        disabilityGroup: data.hasDisability ? (data.disabilityGroup ?? null) : null,
        isWw2Veteran: data.isWw2Veteran,
        isWw2Family: data.isWw2Family,
        documentUrl: documentKey ?? info?.documentUrl ?? null,
      });
      setSaved(true);
      setTimeout(() => setSaved(false), 3000);
    } catch (err) {
      if (err instanceof ApiClientError) setServerError(err.message);
      else setServerError('Произошла ошибка. Попробуйте ещё раз.');
    }
  };

  if (isLoading) return <PageLoader />;

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-base font-semibold text-gray-900">Социальные сведения</h2>
        {info && <DataSourceBadge source={info.source} />}
      </div>

      <div className="bg-white rounded-2xl shadow-card p-5">
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">
              Пенсионный статус
            </label>
            <input
              {...register('pensionStatus')}
              placeholder="Накопительная пенсионная система"
              className="w-full px-3.5 py-2.5 rounded-xl border border-gray-300 text-sm outline-none focus:ring-2 focus:ring-accent-500 focus:border-accent-500"
            />
          </div>

          <div className="space-y-3">
            <label className="flex items-center gap-3 cursor-pointer">
              <input
                {...register('hasDisability')}
                type="checkbox"
                className="w-4 h-4 rounded border-gray-300 text-primary-800 focus:ring-primary-800"
              />
              <span className="text-sm text-gray-700">Имеется инвалидность</span>
            </label>

            {hasDisability && (
              <div className="ml-7">
                <label className="block text-sm font-medium text-gray-700 mb-1.5">
                  Группа инвалидности
                </label>
                <select
                  {...register('disabilityGroup', { valueAsNumber: true })}
                  className="w-full px-3.5 py-2.5 rounded-xl border border-gray-300 text-sm outline-none focus:ring-2 focus:ring-accent-500 focus:border-accent-500 bg-white"
                >
                  <option value="">Не указана</option>
                  <option value={1}>I группа</option>
                  <option value={2}>II группа</option>
                  <option value={3}>III группа</option>
                </select>
              </div>
            )}

            <label className="flex items-center gap-3 cursor-pointer">
              <input
                {...register('isWw2Veteran')}
                type="checkbox"
                className="w-4 h-4 rounded border-gray-300 text-primary-800 focus:ring-primary-800"
              />
              <span className="text-sm text-gray-700">Ветеран ВОВ</span>
            </label>

            <label className="flex items-center gap-3 cursor-pointer">
              <input
                {...register('isWw2Family')}
                type="checkbox"
                className="w-4 h-4 rounded border-gray-300 text-primary-800 focus:ring-primary-800"
              />
              <span className="text-sm text-gray-700">Член семьи ветерана ВОВ</span>
            </label>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">
              Подтверждающий документ
            </label>
            <DocumentUpload
              getUploadUrl={getDocumentUploadUrl}
              onUploaded={(key) => setDocumentKey(key)}
            />
          </div>

          {serverError && (
            <div className="rounded-xl bg-danger-50 border border-danger-200 px-4 py-3">
              <p className="text-sm text-danger-700">{serverError}</p>
            </div>
          )}
          {saved && (
            <div className="rounded-xl bg-success-50 border border-success-200 px-4 py-3">
              <p className="text-sm text-success-700">Данные сохранены успешно.</p>
            </div>
          )}

          <button
            type="submit"
            disabled={isPending || !isDirty}
            className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-primary-800 text-white text-sm font-medium hover:bg-primary-900 transition-colors disabled:opacity-60"
          >
            {isPending ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
            {isPending ? 'Сохранение…' : 'Сохранить'}
          </button>
        </form>
      </div>
    </div>
  );
}
