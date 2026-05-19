'use client';

import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { RefreshCw, Lock, Loader2, Save, FileEdit } from 'lucide-react';
import { clsx } from 'clsx';
import { useAuth } from '@corp-portal/ui-core';
import { usePersonalData, useUpdatePersonalData } from '@/lib/hooks/usePersonalData';
import { DataSourceBadge } from '@/components/personal-data/DataSourceBadge';
import { ChangeRequestModal } from '@/components/personal-data/ChangeRequestModal';
import { PageLoader } from '@/components/ui/LoadingSpinner';
import { ApiClientError } from '@/lib/api/client';
import { ChangeRequestSection } from '@corp-portal/shared-types';
import { formatDateRu } from '@corp-portal/ui-core';

const schema = z.object({
  firstNameEn: z.string().optional(),
  lastNameEn: z.string().optional(),
  middleNameEn: z.string().optional(),
  gender: z.enum(['male', 'female']).optional(),
  nationality: z.string().optional(),
  placeOfBirth: z.string().optional(),
  maritalStatus: z.enum(['single', 'married', 'divorced', 'widowed']).optional(),
});

type FormData = z.infer<typeof schema>;

const GENDER_LABELS: Record<string, string> = {
  male: 'Мужской',
  female: 'Женский',
};

const MARITAL_LABELS: Record<string, string> = {
  single: 'Не женат / Не замужем',
  married: 'Женат / Замужем',
  divorced: 'Разведён / Разведена',
  widowed: 'Вдовец / Вдова',
};

interface ChangeRequestState {
  fieldName: string;
  fieldLabel: string;
  oldValue: string;
}

function ReadOnlyField({
  label,
  value,
}: {
  label: string;
  value?: string | null;
}) {
  return (
    <div>
      <label className="block text-xs font-medium text-gray-500 mb-1">{label}</label>
      <div className="flex items-center gap-2 px-3.5 py-2.5 bg-gray-50 border border-gray-200 rounded-xl">
        <Lock className="w-3.5 h-3.5 text-gray-400 flex-shrink-0" />
        <span className="text-sm text-gray-700 flex-1">{value || '—'}</span>
        <span title="Данные из 1С:ЗУП">
          <RefreshCw className="w-3.5 h-3.5 text-blue-400 flex-shrink-0" />
        </span>
      </div>
    </div>
  );
}

export default function BasicDataPage() {
  const { user, employee } = useAuth();
  const { data: personalData, isLoading } = usePersonalData();
  const { mutateAsync: save, isPending: saving } = useUpdatePersonalData();

  const [changeRequest, setChangeRequest] = useState<ChangeRequestState | null>(null);
  const [serverError, setServerError] = useState<string | null>(null);
  const [saved, setSaved] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors, isDirty },
  } = useForm<FormData>({
    resolver: zodResolver(schema),
    values: {
      firstNameEn: personalData?.firstNameEn ?? '',
      lastNameEn: personalData?.lastNameEn ?? '',
      middleNameEn: personalData?.middleNameEn ?? '',
      gender: (personalData?.gender as FormData['gender']) ?? undefined,
      nationality: personalData?.nationality ?? '',
      placeOfBirth: personalData?.placeOfBirth ?? '',
      maritalStatus: (personalData?.maritalStatus as FormData['maritalStatus']) ?? undefined,
    },
  });

  const onSubmit = async (data: FormData) => {
    setServerError(null);
    try {
      await save(data);
      setSaved(true);
      setTimeout(() => setSaved(false), 3000);
    } catch (err) {
      if (err instanceof ApiClientError) {
        setServerError(err.message);
      } else {
        setServerError('Произошла ошибка. Попробуйте ещё раз.');
      }
    }
  };

  if (isLoading) return <PageLoader />;

  const emp = employee as {
    firstName?: string;
    lastName?: string;
    middleName?: string | null;
    iin?: string | null;
    birthDate?: string | null;
  } | null;

  // Mask IIN: ****789012
  const maskedIin = emp?.iin
    ? '****' + emp.iin.slice(4)
    : null;

  return (
    <div className="space-y-5">
      <div className="bg-white rounded-2xl shadow-card p-5 space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-base font-semibold text-gray-900">Основные данные</h2>
          {personalData && <DataSourceBadge source={personalData.source} />}
        </div>

        <div className="bg-blue-50 border border-blue-200 rounded-xl px-4 py-3 text-xs text-blue-800">
          Поля с иконкой <RefreshCw className="w-3 h-3 inline text-blue-500 mx-0.5" /> синхронизируются из 1С:ЗУП автоматически и недоступны для прямого редактирования.
        </div>

        {/* Read-only fields from 1C / employee */}
        <div className="space-y-3">
          <ReadOnlyField label="Фамилия (из системы)" value={emp?.lastName} />
          <ReadOnlyField label="Имя (из системы)" value={emp?.firstName} />
          <ReadOnlyField label="Отчество (из системы)" value={emp?.middleName} />
          <ReadOnlyField label="ИИН" value={maskedIin} />
          <ReadOnlyField
            label="Дата рождения"
            value={emp?.birthDate ? formatDateRu(emp.birthDate) : null}
          />
        </div>

        <hr className="border-gray-100" />

        {/* Editable user fields */}
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <p className="text-xs text-gray-500 font-medium uppercase tracking-wide">
            Дополнительные данные
          </p>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">
                Имя (латиницей)
              </label>
              <div className="relative">
                <input
                  {...register('firstNameEn')}
                  placeholder="First Name"
                  className={clsx(
                    'w-full px-3.5 py-2.5 rounded-xl border text-sm outline-none transition-colors focus:ring-2 focus:ring-accent-500 focus:border-accent-500',
                    errors.firstNameEn ? 'border-danger-500 bg-danger-50' : 'border-gray-300'
                  )}
                />
                {personalData?.firstNameEn && (
                  <button
                    type="button"
                    onClick={() =>
                      setChangeRequest({
                        fieldName: 'firstNameEn',
                        fieldLabel: 'Имя (латиницей)',
                        oldValue: personalData.firstNameEn ?? '',
                      })
                    }
                    className="absolute right-2 top-1/2 -translate-y-1/2 p-1.5 rounded-lg hover:bg-gray-100 transition-colors"
                    title="Подать заявку на изменение"
                  >
                    <FileEdit className="w-3.5 h-3.5 text-gray-400" />
                  </button>
                )}
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">
                Фамилия (латиницей)
              </label>
              <div className="relative">
                <input
                  {...register('lastNameEn')}
                  placeholder="Last Name"
                  className={clsx(
                    'w-full px-3.5 py-2.5 rounded-xl border text-sm outline-none transition-colors focus:ring-2 focus:ring-accent-500 focus:border-accent-500',
                    errors.lastNameEn ? 'border-danger-500 bg-danger-50' : 'border-gray-300'
                  )}
                />
                {personalData?.lastNameEn && (
                  <button
                    type="button"
                    onClick={() =>
                      setChangeRequest({
                        fieldName: 'lastNameEn',
                        fieldLabel: 'Фамилия (латиницей)',
                        oldValue: personalData.lastNameEn ?? '',
                      })
                    }
                    className="absolute right-2 top-1/2 -translate-y-1/2 p-1.5 rounded-lg hover:bg-gray-100 transition-colors"
                  >
                    <FileEdit className="w-3.5 h-3.5 text-gray-400" />
                  </button>
                )}
              </div>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">
              Отчество (латиницей)
            </label>
            <input
              {...register('middleNameEn')}
              placeholder="Middle Name"
              className="w-full px-3.5 py-2.5 rounded-xl border border-gray-300 text-sm outline-none transition-colors focus:ring-2 focus:ring-accent-500 focus:border-accent-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">Пол</label>
            <select
              {...register('gender')}
              className="w-full px-3.5 py-2.5 rounded-xl border border-gray-300 text-sm outline-none transition-colors focus:ring-2 focus:ring-accent-500 focus:border-accent-500 bg-white"
            >
              <option value="">Не указан</option>
              {Object.entries(GENDER_LABELS).map(([val, label]) => (
                <option key={val} value={val}>
                  {label}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">
              Национальность
            </label>
            <div className="relative">
              <input
                {...register('nationality')}
                placeholder="Казахская"
                className="w-full px-3.5 py-2.5 rounded-xl border border-gray-300 text-sm outline-none transition-colors focus:ring-2 focus:ring-accent-500 focus:border-accent-500"
              />
              {personalData?.nationality && (
                <button
                  type="button"
                  onClick={() =>
                    setChangeRequest({
                      fieldName: 'nationality',
                      fieldLabel: 'Национальность',
                      oldValue: personalData.nationality ?? '',
                    })
                  }
                  className="absolute right-2 top-1/2 -translate-y-1/2 p-1.5 rounded-lg hover:bg-gray-100 transition-colors"
                >
                  <FileEdit className="w-3.5 h-3.5 text-gray-400" />
                </button>
              )}
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">
              Место рождения
            </label>
            <div className="relative">
              <input
                {...register('placeOfBirth')}
                placeholder="г. Алматы"
                className="w-full px-3.5 py-2.5 rounded-xl border border-gray-300 text-sm outline-none transition-colors focus:ring-2 focus:ring-accent-500 focus:border-accent-500"
              />
              {personalData?.placeOfBirth && (
                <button
                  type="button"
                  onClick={() =>
                    setChangeRequest({
                      fieldName: 'placeOfBirth',
                      fieldLabel: 'Место рождения',
                      oldValue: personalData.placeOfBirth ?? '',
                    })
                  }
                  className="absolute right-2 top-1/2 -translate-y-1/2 p-1.5 rounded-lg hover:bg-gray-100 transition-colors"
                >
                  <FileEdit className="w-3.5 h-3.5 text-gray-400" />
                </button>
              )}
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">
              Семейное положение
            </label>
            <select
              {...register('maritalStatus')}
              className="w-full px-3.5 py-2.5 rounded-xl border border-gray-300 text-sm outline-none transition-colors focus:ring-2 focus:ring-accent-500 focus:border-accent-500 bg-white"
            >
              <option value="">Не указано</option>
              {Object.entries(MARITAL_LABELS).map(([val, label]) => (
                <option key={val} value={val}>
                  {label}
                </option>
              ))}
            </select>
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
            disabled={saving || !isDirty}
            className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-primary-800 text-white text-sm font-medium hover:bg-primary-900 transition-colors disabled:opacity-60"
          >
            {saving ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Save className="w-4 h-4" />
            )}
            {saving ? 'Сохранение…' : 'Сохранить'}
          </button>
        </form>
      </div>

      {changeRequest && (
        <ChangeRequestModal
          section={ChangeRequestSection.BasicData}
          fieldName={changeRequest.fieldName}
          fieldLabel={changeRequest.fieldLabel}
          oldValue={changeRequest.oldValue}
          onClose={() => setChangeRequest(null)}
        />
      )}
    </div>
  );
}
