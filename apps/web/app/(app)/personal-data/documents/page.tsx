'use client';

import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import {
  Plus,
  Download,
  AlertTriangle,
  Loader2,
  CreditCard,
  X,
} from 'lucide-react';
import { useDocuments, useAddDocument } from '@/lib/hooks/usePersonalData';
import { DocumentUpload } from '@/components/personal-data/DocumentUpload';
import { DataSourceBadge } from '@/components/personal-data/DataSourceBadge';
import { PageLoader } from '@/components/ui/LoadingSpinner';
import { getDocumentUploadUrl, getDocumentDownloadUrl } from '@/lib/api/personalData';
import { ApiClientError } from '@/lib/api/client';
import { clsx } from 'clsx';
import type { IdentityDocument } from '@corp-portal/shared-types';

const DOC_TYPE_LABELS: Record<IdentityDocument['documentType'], string> = {
  national_id: 'Удостоверение личности',
  passport: 'Паспорт',
  residence_permit: 'Вид на жительство',
  other: 'Другое',
};

const schema = z.object({
  documentType: z.enum(['national_id', 'passport', 'residence_permit', 'other']),
  series: z.string().optional(),
  number: z.string().min(1, 'Введите номер документа'),
  issuedBy: z.string().min(1, 'Укажите кем выдан'),
  issueDate: z.string().min(1, 'Укажите дату выдачи'),
  expiryDate: z.string().optional(),
});

type FormData = z.infer<typeof schema>;

function isExpiringSoon(expiryDate: string | null): boolean {
  if (!expiryDate) return false;
  const diff = new Date(expiryDate).getTime() - Date.now();
  return diff < 30 * 24 * 60 * 60 * 1000 && diff > 0;
}

function isExpired(expiryDate: string | null): boolean {
  if (!expiryDate) return false;
  return new Date(expiryDate) < new Date();
}

export default function DocumentsPage() {
  const { data: documents, isLoading, refetch } = useDocuments();
  const { mutateAsync: addDoc, isPending } = useAddDocument();
  const [showForm, setShowForm] = useState(false);
  const [documentKey, setDocumentKey] = useState<string | null>(null);
  const [docError, setDocError] = useState<string | null>(null);
  const [serverError, setServerError] = useState<string | null>(null);
  const [downloading, setDownloading] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: { documentType: 'national_id' },
  });

  const handleDownload = async (id: string) => {
    setDownloading(id);
    try {
      const { url } = await getDocumentDownloadUrl(id);
      window.open(url, '_blank');
    } finally {
      setDownloading(null);
    }
  };

  const onSubmit = async (data: FormData) => {
    if (!documentKey) {
      setDocError('Прикрепите скан документа');
      return;
    }
    setDocError(null);
    setServerError(null);
    try {
      await addDoc({
        documentType: data.documentType,
        series: data.series ?? null,
        number: data.number,
        issuedBy: data.issuedBy,
        issueDate: data.issueDate,
        expiryDate: data.expiryDate ?? null,
        documentUrl: documentKey,
        isActive: true,
      });
      reset();
      setDocumentKey(null);
      setShowForm(false);
    } catch (err) {
      if (err instanceof ApiClientError) {
        setServerError(err.message);
      } else {
        setServerError('Произошла ошибка. Попробуйте ещё раз.');
      }
    }
  };

  if (isLoading) return <PageLoader />;

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-base font-semibold text-gray-900">Удостоверения личности</h2>
        <button
          onClick={() => setShowForm(!showForm)}
          className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-primary-800 text-white text-sm font-medium hover:bg-primary-900 transition-colors"
        >
          <Plus className="w-4 h-4" />
          Добавить
        </button>
      </div>

      {/* Document list */}
      {documents?.length === 0 && !showForm && (
        <div className="bg-white rounded-2xl shadow-card p-8 text-center">
          <CreditCard className="w-8 h-8 text-gray-300 mx-auto mb-3" />
          <p className="text-sm font-medium text-gray-900 mb-1">Документы не добавлены</p>
          <p className="text-xs text-gray-400 mb-4">Добавьте удостоверение личности или паспорт</p>
          <button
            onClick={() => setShowForm(true)}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-primary-800 text-white text-sm font-medium hover:bg-primary-900 transition-colors"
          >
            <Plus className="w-4 h-4" />
            Добавить документ
          </button>
        </div>
      )}

      <div className="space-y-3">
        {documents?.map((doc) => (
          <div key={doc.id} className="bg-white rounded-2xl shadow-card p-4">
            <div className="flex items-start justify-between gap-3">
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 flex-wrap">
                  <p className="text-sm font-semibold text-gray-900">
                    {DOC_TYPE_LABELS[doc.documentType]}
                  </p>
                  <DataSourceBadge source={doc.source} />
                  {isExpired(doc.expiryDate) && (
                    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-danger-100 text-danger-700 border border-danger-200">
                      <AlertTriangle className="w-3 h-3" />
                      Просрочен
                    </span>
                  )}
                  {!isExpired(doc.expiryDate) && isExpiringSoon(doc.expiryDate) && (
                    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-warning-100 text-warning-700 border border-warning-200">
                      <AlertTriangle className="w-3 h-3" />
                      Истекает скоро
                    </span>
                  )}
                </div>

                <div className="mt-2 grid grid-cols-2 gap-x-4 gap-y-1 text-xs text-gray-500">
                  {doc.series && (
                    <div>
                      <span className="text-gray-400">Серия: </span>
                      <span className="text-gray-700 font-medium">{doc.series}</span>
                    </div>
                  )}
                  <div>
                    <span className="text-gray-400">Номер: </span>
                    <span className="text-gray-700 font-medium">{doc.number}</span>
                  </div>
                  <div className="col-span-2">
                    <span className="text-gray-400">Кем выдан: </span>
                    <span className="text-gray-700">{doc.issuedBy}</span>
                  </div>
                  <div>
                    <span className="text-gray-400">Дата выдачи: </span>
                    <span className="text-gray-700">{new Date(doc.issueDate).toLocaleDateString('ru-RU')}</span>
                  </div>
                  {doc.expiryDate && (
                    <div>
                      <span className="text-gray-400">Срок: </span>
                      <span className={clsx('font-medium', isExpired(doc.expiryDate) ? 'text-danger-700' : isExpiringSoon(doc.expiryDate) ? 'text-warning-700' : 'text-gray-700')}>
                        {new Date(doc.expiryDate).toLocaleDateString('ru-RU')}
                      </span>
                    </div>
                  )}
                </div>
              </div>

              {doc.documentUrl && (
                <button
                  onClick={() => void handleDownload(doc.id)}
                  disabled={downloading === doc.id}
                  className="p-2 rounded-xl hover:bg-gray-100 transition-colors flex-shrink-0"
                  title="Скачать документ"
                >
                  {downloading === doc.id ? (
                    <Loader2 className="w-4 h-4 text-gray-400 animate-spin" />
                  ) : (
                    <Download className="w-4 h-4 text-gray-400" />
                  )}
                </button>
              )}
            </div>
          </div>
        ))}
      </div>

      {/* Add form */}
      {showForm && (
        <div className="bg-white rounded-2xl shadow-card p-5 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold text-gray-900">Новый документ</h3>
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
                Тип документа <span className="text-danger-500">*</span>
              </label>
              <select
                {...register('documentType')}
                className="w-full px-3.5 py-2.5 rounded-xl border border-gray-300 text-sm outline-none focus:ring-2 focus:ring-accent-500 focus:border-accent-500 bg-white"
              >
                {Object.entries(DOC_TYPE_LABELS).map(([val, label]) => (
                  <option key={val} value={val}>
                    {label}
                  </option>
                ))}
              </select>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1.5">Серия</label>
                <input
                  {...register('series')}
                  placeholder="AB"
                  className="w-full px-3.5 py-2.5 rounded-xl border border-gray-300 text-sm outline-none focus:ring-2 focus:ring-accent-500 focus:border-accent-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1.5">
                  Номер <span className="text-danger-500">*</span>
                </label>
                <input
                  {...register('number')}
                  placeholder="1234567"
                  className={clsx(
                    'w-full px-3.5 py-2.5 rounded-xl border text-sm outline-none focus:ring-2 focus:ring-accent-500 focus:border-accent-500',
                    errors.number ? 'border-danger-500 bg-danger-50' : 'border-gray-300'
                  )}
                />
                {errors.number && (
                  <p className="mt-1 text-xs text-danger-600">{errors.number.message}</p>
                )}
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">
                Кем выдан <span className="text-danger-500">*</span>
              </label>
              <input
                {...register('issuedBy')}
                placeholder="МВД РК, г. Алматы"
                className={clsx(
                  'w-full px-3.5 py-2.5 rounded-xl border text-sm outline-none focus:ring-2 focus:ring-accent-500 focus:border-accent-500',
                  errors.issuedBy ? 'border-danger-500 bg-danger-50' : 'border-gray-300'
                )}
              />
              {errors.issuedBy && (
                <p className="mt-1 text-xs text-danger-600">{errors.issuedBy.message}</p>
              )}
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1.5">
                  Дата выдачи <span className="text-danger-500">*</span>
                </label>
                <input
                  {...register('issueDate')}
                  type="date"
                  className={clsx(
                    'w-full px-3.5 py-2.5 rounded-xl border text-sm outline-none focus:ring-2 focus:ring-accent-500 focus:border-accent-500',
                    errors.issueDate ? 'border-danger-500 bg-danger-50' : 'border-gray-300'
                  )}
                />
                {errors.issueDate && (
                  <p className="mt-1 text-xs text-danger-600">{errors.issueDate.message}</p>
                )}
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1.5">
                  Срок действия
                </label>
                <input
                  {...register('expiryDate')}
                  type="date"
                  className="w-full px-3.5 py-2.5 rounded-xl border border-gray-300 text-sm outline-none focus:ring-2 focus:ring-accent-500 focus:border-accent-500"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">
                Скан документа <span className="text-danger-500">*</span>
              </label>
              <DocumentUpload
                getUploadUrl={getDocumentUploadUrl}
                onUploaded={(key) => {
                  setDocumentKey(key);
                  setDocError(null);
                }}
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
                disabled={isPending}
                className="flex-1 flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl bg-primary-800 text-white text-sm font-medium hover:bg-primary-900 transition-colors disabled:opacity-60"
              >
                {isPending ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : null}
                {isPending ? 'Сохранение…' : 'Добавить'}
              </button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
}
