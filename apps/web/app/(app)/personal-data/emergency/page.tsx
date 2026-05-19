'use client';

import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Loader2, Save, Phone, Info } from 'lucide-react';
import { clsx } from 'clsx';
import { useEmergencyContact, useUpdateEmergencyContact } from '@/lib/hooks/usePersonalData';
import { PageLoader } from '@/components/ui/LoadingSpinner';
import { ApiClientError } from '@/lib/api/client';

const schema = z.object({
  fullName: z.string().min(1, 'Введите полное имя'),
  phone: z.string().min(1, 'Введите номер телефона'),
  address: z.string().optional(),
  relationship: z.string().min(1, 'Укажите кем приходится'),
});

type FormData = z.infer<typeof schema>;

export default function EmergencyPage() {
  const { data: contact, isLoading } = useEmergencyContact();
  const { mutateAsync: update, isPending } = useUpdateEmergencyContact();

  const [serverError, setServerError] = useState<string | null>(null);
  const [saved, setSaved] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors, isDirty },
  } = useForm<FormData>({
    resolver: zodResolver(schema),
    values: {
      fullName: contact?.fullName ?? '',
      phone: contact?.phone ?? '',
      address: contact?.address ?? '',
      relationship: contact?.relationship ?? '',
    },
  });

  const onSubmit = async (data: FormData) => {
    setServerError(null);
    try {
      await update({
        fullName: data.fullName,
        phone: data.phone,
        address: data.address ?? null,
        relationship: data.relationship,
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
      <h2 className="text-base font-semibold text-gray-900">Экстренный контакт</h2>

      <div className="flex gap-3 bg-blue-50 border border-blue-200 rounded-xl px-4 py-3">
        <Info className="w-4 h-4 text-blue-600 flex-shrink-0 mt-0.5" />
        <p className="text-sm text-blue-800">
          Данный контакт используется при возникновении несчастного случая на производстве.
        </p>
      </div>

      <div className="bg-white rounded-2xl shadow-card p-5">
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">
              Полное имя (ФИО) <span className="text-danger-500">*</span>
            </label>
            <input
              {...register('fullName')}
              placeholder="Иванова Мария Петровна"
              className={clsx(
                'w-full px-3.5 py-2.5 rounded-xl border text-sm outline-none focus:ring-2 focus:ring-accent-500 focus:border-accent-500',
                errors.fullName ? 'border-danger-500 bg-danger-50' : 'border-gray-300'
              )}
            />
            {errors.fullName && (
              <p className="mt-1 text-xs text-danger-600">{errors.fullName.message}</p>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">
              Номер телефона <span className="text-danger-500">*</span>
            </label>
            <div className="relative">
              <Phone className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
              <input
                {...register('phone')}
                type="tel"
                placeholder="+7 777 123 45 67"
                className={clsx(
                  'w-full pl-9 pr-3.5 py-2.5 rounded-xl border text-sm outline-none focus:ring-2 focus:ring-accent-500 focus:border-accent-500',
                  errors.phone ? 'border-danger-500 bg-danger-50' : 'border-gray-300'
                )}
              />
            </div>
            {errors.phone && (
              <p className="mt-1 text-xs text-danger-600">{errors.phone.message}</p>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">
              Кем приходится <span className="text-danger-500">*</span>
            </label>
            <input
              {...register('relationship')}
              placeholder="Жена, Мать, Брат…"
              className={clsx(
                'w-full px-3.5 py-2.5 rounded-xl border text-sm outline-none focus:ring-2 focus:ring-accent-500 focus:border-accent-500',
                errors.relationship ? 'border-danger-500 bg-danger-50' : 'border-gray-300'
              )}
            />
            {errors.relationship && (
              <p className="mt-1 text-xs text-danger-600">{errors.relationship.message}</p>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">Адрес</label>
            <input
              {...register('address')}
              placeholder="г. Алматы, ул. Абая 12, кв. 45"
              className="w-full px-3.5 py-2.5 rounded-xl border border-gray-300 text-sm outline-none focus:ring-2 focus:ring-accent-500 focus:border-accent-500"
            />
          </div>

          {serverError && (
            <div className="rounded-xl bg-danger-50 border border-danger-200 px-4 py-3">
              <p className="text-sm text-danger-700">{serverError}</p>
            </div>
          )}
          {saved && (
            <div className="rounded-xl bg-success-50 border border-success-200 px-4 py-3">
              <p className="text-sm text-success-700">Контакт сохранён успешно.</p>
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
