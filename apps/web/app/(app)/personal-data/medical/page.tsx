'use client';

import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Plus, Trash2, FileText, Loader2, Download, X } from 'lucide-react';
import { clsx } from 'clsx';
import { useMedicalCerts, useAddMedicalCert, useDeleteMedicalCert } from '@/lib/hooks/usePersonalData';
import { DocumentUpload } from '@/components/personal-data/DocumentUpload';
import { PageLoader } from '@/components/ui/LoadingSpinner';
import { getMedicalCertUploadUrl } from '@/lib/api/personalData';
import { ApiClientError } from '@/lib/api/client';
import type { MedicalCertificate } from '@corp-portal/shared-types';

const CERT_TYPE_LABELS: Record<MedicalCertificate['certType'], string> = {
  narco_dispensary: 'Наркологический диспансер',
  psycho_dispensary: 'Психиатрический диспансер',
  form_075: 'Форма 075 (медкнижка)',
};

const schema = z.object({
  certType: z.enum(['narco_dispensary', 'psycho_dispensary', 'form_075']),
  certNumber: z.string().min(1, 'Укажите номер справки'),
  issueDate: z.string().min(1, 'Укажите дату выдачи'),
  expiryDate: z.string().optional(),
});

type FormData = z.infer<typeof schema>;

type CertType = MedicalCertificate['certType'];

const CERT_TYPES: CertType[] = ['narco_dispensary', 'psycho_dispensary', 'form_075'];

function CertSection({
  certType,
  certs,
}: {
  certType: CertType;
  certs: MedicalCertificate[];
}) {
  const { mutateAsync: add, isPending: adding } = useAddMedicalCert();
  const { mutateAsync: remove } = useDeleteMedicalCert();

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
    defaultValues: { certType },
  });

  const onSubmit = async (data: FormData) => {
    if (!documentKey) {
      setDocError('Прикрепите скан справки');
      return;
    }
    setDocError(null);
    setServerError(null);
    try {
      await add({
        certType: data.certType,
        certNumber: data.certNumber,
        issueDate: data.issueDate,
        expiryDate: data.expiryDate ?? null,
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

  const relevantCerts = certs.filter((c) => c.certType === certType);

  return (
    <div className="bg-white rounded-2xl shadow-card overflow-hidden">
      <div className="flex items-center justify-between px-5 py-3 border-b border-gray-50">
        <h3 className="text-sm font-semibold text-gray-700">{CERT_TYPE_LABELS[certType]}</h3>
        <button
          onClick={() => setShowForm(!showForm)}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-gray-100 text-gray-700 text-xs font-medium hover:bg-gray-200 transition-colors"
        >
          <Plus className="w-3.5 h-3.5" />
          Добавить
        </button>
      </div>

      {relevantCerts.length === 0 && !showForm && (
        <div className="px-5 py-4 text-center">
          <FileText className="w-5 h-5 text-gray-300 mx-auto mb-1" />
          <p className="text-sm text-gray-400">Справка не добавлена</p>
        </div>
      )}

      <div className="divide-y divide-gray-50">
        {relevantCerts.map((cert) => (
          <div key={cert.id} className="flex items-center justify-between gap-3 px-5 py-3.5">
            <div>
              <p className="text-sm text-gray-900 font-medium">
                № {cert.certNumber}
              </p>
              <p className="text-xs text-gray-500">
                Выдана: {new Date(cert.issueDate).toLocaleDateString('ru-RU')}
                {cert.expiryDate && ` · до ${new Date(cert.expiryDate).toLocaleDateString('ru-RU')}`}
              </p>
            </div>
            <div className="flex items-center gap-2">
              <a
                href={cert.documentUrl}
                target="_blank"
                rel="noreferrer"
                className="p-2 rounded-xl hover:bg-gray-100 transition-colors"
                title="Скачать"
              >
                <Download className="w-4 h-4 text-gray-400" />
              </a>
              <button
                onClick={() => void handleDelete(cert.id)}
                disabled={deletingId === cert.id}
                className="p-2 rounded-xl hover:bg-danger-50 transition-colors"
              >
                {deletingId === cert.id ? (
                  <Loader2 className="w-4 h-4 animate-spin text-gray-400" />
                ) : (
                  <Trash2 className="w-4 h-4 text-gray-400 hover:text-danger-600" />
                )}
              </button>
            </div>
          </div>
        ))}
      </div>

      {showForm && (
        <div className="px-5 py-4 border-t border-gray-100 space-y-4">
          <div className="flex items-center justify-between">
            <p className="text-sm font-semibold text-gray-900">Новая справка</p>
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

          <form onSubmit={handleSubmit(onSubmit)} className="space-y-3">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">
                Номер справки <span className="text-danger-500">*</span>
              </label>
              <input
                {...register('certNumber')}
                placeholder="123456"
                className={clsx(
                  'w-full px-3.5 py-2.5 rounded-xl border text-sm outline-none focus:ring-2 focus:ring-accent-500 focus:border-accent-500',
                  errors.certNumber ? 'border-danger-500 bg-danger-50' : 'border-gray-300'
                )}
              />
              {errors.certNumber && (
                <p className="mt-1 text-xs text-danger-600">{errors.certNumber.message}</p>
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
                Скан справки <span className="text-danger-500">*</span>
              </label>
              <DocumentUpload
                getUploadUrl={getMedicalCertUploadUrl}
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

export default function MedicalPage() {
  const { data: certs, isLoading } = useMedicalCerts();

  if (isLoading) return <PageLoader />;

  return (
    <div className="space-y-4">
      <h2 className="text-base font-semibold text-gray-900">Медицинские справки</h2>
      {CERT_TYPES.map((type) => (
        <CertSection key={type} certType={type} certs={certs ?? []} />
      ))}
    </div>
  );
}
