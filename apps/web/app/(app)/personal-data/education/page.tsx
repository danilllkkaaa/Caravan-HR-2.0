'use client';

import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Plus, Trash2, GraduationCap, Loader2, X } from 'lucide-react';
import { clsx } from 'clsx';
import { useEducation, useAddEducation, useDeleteEducation } from '@/lib/hooks/usePersonalData';
import { DataSourceBadge } from '@/components/personal-data/DataSourceBadge';
import { DocumentUpload } from '@/components/personal-data/DocumentUpload';
import { PageLoader } from '@/components/ui/LoadingSpinner';
import { getDocumentUploadUrl } from '@/lib/api/personalData';
import { ApiClientError } from '@/lib/api/client';
import type { EducationRecord } from '@corp-portal/shared-types';

const EDU_TYPE_LABELS: Record<EducationRecord['educationType'], string> = {
  higher: 'Высшее',
  secondary: 'Среднее',
  technical: 'Среднее специальное',
  advanced_qualification: 'Повышение квалификации',
  other: 'Другое',
};

const schema = z.object({
  educationType: z.enum(['higher', 'secondary', 'technical', 'advanced_qualification', 'other']),
  institutionName: z.string().min(1, 'Укажите учебное заведение'),
  specialty: z.string().optional(),
  qualification: z.string().optional(),
  graduationDate: z.string().optional(),
  documentNumber: z.string().optional(),
});

type FormData = z.infer<typeof schema>;

export default function EducationPage() {
  const { data: education, isLoading } = useEducation();
  const { mutateAsync: add, isPending: adding } = useAddEducation();
  const { mutateAsync: remove, isPending: removing } = useDeleteEducation();

  const [showForm, setShowForm] = useState(false);
  const [documentKey, setDocumentKey] = useState<string | null>(null);
  const [docError, setDocError] = useState<string | null>(null);
  const [serverError, setServerError] = useState<string | null>(null);
  const [deletingId, setDeletingId] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: { educationType: 'higher' },
  });

  const onSubmit = async (data: FormData) => {
    setDocError(null);
    setServerError(null);
    try {
      await add({
        educationType: data.educationType,
        institutionName: data.institutionName,
        specialty: data.specialty ?? null,
        qualification: data.qualification ?? null,
        graduationDate: data.graduationDate ?? null,
        documentNumber: data.documentNumber ?? null,
        documentUrl: documentKey,
      });
      reset();
      setDocumentKey(null);
      setShowForm(false);
    } catch (err) {
      if (err instanceof ApiClientError) setServerError(err.message);
      else setServerError('Произошла ошибка. Попробуйте ещё раз.');
    }
  };

  const handleDelete = async (id: string) => {
    setDeletingId(id);
    try {
      await remove(id);
    } finally {
      setDeletingId(null);
    }
  };

  if (isLoading) return <PageLoader />;

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-base font-semibold text-gray-900">Образование</h2>
        <button
          onClick={() => setShowForm(!showForm)}
          className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-primary-800 text-white text-sm font-medium hover:bg-primary-900 transition-colors"
        >
          <Plus className="w-4 h-4" />
          Добавить
        </button>
      </div>

      {education?.length === 0 && !showForm && (
        <div className="bg-white rounded-2xl shadow-card p-8 text-center">
          <GraduationCap className="w-8 h-8 text-gray-300 mx-auto mb-3" />
          <p className="text-sm font-medium text-gray-900 mb-1">Сведения об образовании не добавлены</p>
          <p className="text-xs text-gray-400 mb-4">Добавьте информацию о полученном образовании</p>
          <button
            onClick={() => setShowForm(true)}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-primary-800 text-white text-sm font-medium hover:bg-primary-900 transition-colors"
          >
            <Plus className="w-4 h-4" />
            Добавить образование
          </button>
        </div>
      )}

      <div className="space-y-3">
        {education?.map((edu) => (
          <div key={edu.id} className="bg-white rounded-2xl shadow-card p-4">
            <div className="flex items-start justify-between gap-3">
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 flex-wrap mb-1">
                  <p className="text-sm font-semibold text-gray-900">
                    {EDU_TYPE_LABELS[edu.educationType]}
                  </p>
                  <DataSourceBadge source={edu.source} />
                </div>
                <p className="text-sm text-gray-700">{edu.institutionName}</p>
                {edu.specialty && (
                  <p className="text-xs text-gray-500 mt-1">
                    Специальность: <span className="text-gray-700">{edu.specialty}</span>
                  </p>
                )}
                {edu.qualification && (
                  <p className="text-xs text-gray-500">
                    Квалификация: <span className="text-gray-700">{edu.qualification}</span>
                  </p>
                )}
                {edu.graduationDate && (
                  <p className="text-xs text-gray-500">
                    Год окончания:{' '}
                    <span className="text-gray-700">
                      {new Date(edu.graduationDate).getFullYear()}
                    </span>
                  </p>
                )}
              </div>
              {edu.source === 'user' && (
                <button
                  onClick={() => void handleDelete(edu.id)}
                  disabled={deletingId === edu.id}
                  className="p-2 rounded-xl hover:bg-danger-50 transition-colors flex-shrink-0"
                  title="Удалить"
                >
                  {deletingId === edu.id ? (
                    <Loader2 className="w-4 h-4 text-gray-400 animate-spin" />
                  ) : (
                    <Trash2 className="w-4 h-4 text-gray-400 hover:text-danger-600" />
                  )}
                </button>
              )}
            </div>
          </div>
        ))}
      </div>

      {showForm && (
        <div className="bg-white rounded-2xl shadow-card p-5 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold text-gray-900">Новая запись об образовании</h3>
            <button
              onClick={() => {
                setShowForm(false);
                reset();
                setDocumentKey(null);
              }}
              className="p-1.5 rounded-xl hover:bg-gray-100 transition-colors"
            >
              <X className="w-4 h-4 text-gray-500" />
            </button>
          </div>

          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">
                Вид образования <span className="text-danger-500">*</span>
              </label>
              <select
                {...register('educationType')}
                className="w-full px-3.5 py-2.5 rounded-xl border border-gray-300 text-sm outline-none focus:ring-2 focus:ring-accent-500 focus:border-accent-500 bg-white"
              >
                {Object.entries(EDU_TYPE_LABELS).map(([val, label]) => (
                  <option key={val} value={val}>
                    {label}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">
                Учебное заведение <span className="text-danger-500">*</span>
              </label>
              <input
                {...register('institutionName')}
                placeholder="КазНУ им. аль-Фараби"
                className={clsx(
                  'w-full px-3.5 py-2.5 rounded-xl border text-sm outline-none focus:ring-2 focus:ring-accent-500 focus:border-accent-500',
                  errors.institutionName ? 'border-danger-500 bg-danger-50' : 'border-gray-300'
                )}
              />
              {errors.institutionName && (
                <p className="mt-1 text-xs text-danger-600">{errors.institutionName.message}</p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">Специальность</label>
              <input
                {...register('specialty')}
                placeholder="Информационные системы"
                className="w-full px-3.5 py-2.5 rounded-xl border border-gray-300 text-sm outline-none focus:ring-2 focus:ring-accent-500 focus:border-accent-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">Квалификация</label>
              <input
                {...register('qualification')}
                placeholder="Бакалавр / Магистр"
                className="w-full px-3.5 py-2.5 rounded-xl border border-gray-300 text-sm outline-none focus:ring-2 focus:ring-accent-500 focus:border-accent-500"
              />
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1.5">
                  Дата окончания
                </label>
                <input
                  {...register('graduationDate')}
                  type="date"
                  className="w-full px-3.5 py-2.5 rounded-xl border border-gray-300 text-sm outline-none focus:ring-2 focus:ring-accent-500 focus:border-accent-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1.5">
                  Номер диплома
                </label>
                <input
                  {...register('documentNumber')}
                  placeholder="ДВ 1234567"
                  className="w-full px-3.5 py-2.5 rounded-xl border border-gray-300 text-sm outline-none focus:ring-2 focus:ring-accent-500 focus:border-accent-500"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">
                Скан диплома / документа об образовании
              </label>
              <DocumentUpload
                getUploadUrl={getDocumentUploadUrl}
                onUploaded={(key) => setDocumentKey(key)}
              />
              {docError && <p className="mt-1 text-xs text-danger-600">{docError}</p>}
            </div>

            {serverError && (
              <div className="rounded-xl bg-danger-50 border border-danger-200 px-4 py-3">
                <p className="text-sm text-danger-700">{serverError}</p>
              </div>
            )}

            <div className="flex gap-3">
              <button
                type="button"
                onClick={() => {
                  setShowForm(false);
                  reset();
                  setDocumentKey(null);
                }}
                className="flex-1 px-4 py-2.5 rounded-xl border border-gray-200 text-sm font-medium text-gray-700 hover:bg-gray-50 transition-colors"
              >
                Отмена
              </button>
              <button
                type="submit"
                disabled={adding}
                className="flex-1 flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl bg-primary-800 text-white text-sm font-medium hover:bg-primary-900 transition-colors disabled:opacity-60"
              >
                {adding && <Loader2 className="w-4 h-4 animate-spin" />}
                {adding ? 'Сохранение…' : 'Добавить'}
              </button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
}
