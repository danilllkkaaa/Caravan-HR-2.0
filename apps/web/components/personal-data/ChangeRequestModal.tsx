'use client';

import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { X, Loader2 } from 'lucide-react';
import { useCreateChangeRequest } from '@/lib/hooks/usePersonalData';
import { DocumentUpload } from './DocumentUpload';
import { getMedicalCertUploadUrl } from '@/lib/api/personalData';
import type { ChangeRequestSection } from '@corp-portal/shared-types';
import { ApiClientError } from '@/lib/api/client';

const schema = z.object({
  newValue: z.string().min(1, 'Введите новое значение'),
  comment: z.string().optional(),
});

type FormData = z.infer<typeof schema>;

interface ChangeRequestModalProps {
  section: ChangeRequestSection;
  fieldName: string;
  fieldLabel: string;
  oldValue: string;
  onClose: () => void;
}

export function ChangeRequestModal({
  section,
  fieldName,
  fieldLabel,
  oldValue,
  onClose,
}: ChangeRequestModalProps) {
  const [documentKey, setDocumentKey] = useState<string | null>(null);
  const [docError, setDocError] = useState<string | null>(null);
  const [serverError, setServerError] = useState<string | null>(null);

  const { mutateAsync, isPending } = useCreateChangeRequest();

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<FormData>({ resolver: zodResolver(schema) });

  const onSubmit = async (data: FormData) => {
    if (!documentKey) {
      setDocError('Прикрепите подтверждающий документ');
      return;
    }
    setDocError(null);
    setServerError(null);

    try {
      await mutateAsync({
        section,
        fieldName,
        oldValue: { [fieldName]: oldValue },
        newValue: { [fieldName]: data.newValue },
        comment: data.comment ?? undefined,
        documentUrl: documentKey,
      });
      onClose();
    } catch (err) {
      if (err instanceof ApiClientError) {
        setServerError(err.message);
      } else {
        setServerError('Произошла ошибка. Попробуйте ещё раз.');
      }
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-end sm:items-center justify-center p-4 bg-black/40 backdrop-blur-sm">
      <div className="w-full max-w-md bg-white rounded-2xl shadow-xl">
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-4 border-b border-gray-100">
          <h2 className="text-base font-semibold text-gray-900">Заявка на изменение</h2>
          <button
            onClick={onClose}
            className="w-8 h-8 flex items-center justify-center rounded-xl hover:bg-gray-100 transition-colors"
          >
            <X className="w-4 h-4 text-gray-500" />
          </button>
        </div>

        <form onSubmit={handleSubmit(onSubmit)} className="p-5 space-y-4">
          {/* Current value */}
          <div>
            <p className="text-xs text-gray-500 mb-1">Поле</p>
            <p className="text-sm font-medium text-gray-900">{fieldLabel}</p>
          </div>

          <div className="bg-gray-50 rounded-xl px-4 py-3">
            <p className="text-xs text-gray-500 mb-0.5">Текущее значение</p>
            <p className="text-sm text-gray-700">{oldValue || '—'}</p>
          </div>

          {/* New value */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">
              Новое значение <span className="text-danger-500">*</span>
            </label>
            <textarea
              {...register('newValue')}
              rows={3}
              placeholder="Введите корректное значение"
              className="w-full px-3.5 py-2.5 rounded-xl border border-gray-300 text-sm outline-none transition-colors focus:ring-2 focus:ring-accent-500 focus:border-accent-500 resize-none"
            />
            {errors.newValue && (
              <p className="mt-1 text-xs text-danger-600">{errors.newValue.message}</p>
            )}
          </div>

          {/* Comment */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">
              Комментарий
            </label>
            <textarea
              {...register('comment')}
              rows={2}
              placeholder="Причина изменения (необязательно)"
              className="w-full px-3.5 py-2.5 rounded-xl border border-gray-300 text-sm outline-none transition-colors focus:ring-2 focus:ring-accent-500 focus:border-accent-500 resize-none"
            />
          </div>

          {/* Document upload */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">
              Подтверждающий документ <span className="text-danger-500">*</span>
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

          <div className="flex gap-3 pt-1">
            <button
              type="button"
              onClick={onClose}
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
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Отправка…
                </>
              ) : (
                'Подать заявку'
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
