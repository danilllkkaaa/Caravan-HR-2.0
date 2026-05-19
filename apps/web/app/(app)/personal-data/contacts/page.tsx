'use client';

import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Mail, Phone, Save, Loader2 } from 'lucide-react';
import { useContacts, useUpdateContacts } from '@/lib/hooks/usePersonalData';
import { PageLoader } from '@/components/ui/LoadingSpinner';
import clsx from 'clsx';

const phoneSchema = z
  .string()
  .optional()
  .nullable()
  .refine((value) => {
    if (!value) return true;
    const normalized = value.replace(/[\s\-()]/g, '').replace(/^\+/, '');
    return /^\d{7,15}$/.test(normalized);
  }, 'Введите телефон в международном формате');

const schema = z.object({
  email: z.string().email('Введите корректный email'),
  mobilePhone: z.string().min(1, 'Укажите мобильный телефон').pipe(phoneSchema),
  homePhone: phoneSchema,
  additionalPhone: phoneSchema,
});

type FormData = z.infer<typeof schema>;

export default function ContactsPage() {
  const { data: contacts, isLoading } = useContacts();
  const { mutateAsync: update, isPending } = useUpdateContacts();

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitSuccessful },
  } = useForm<FormData>({
    resolver: zodResolver(schema),
    values: {
      email: contacts?.email ?? '',
      mobilePhone: contacts?.mobilePhone ?? '',
      homePhone: contacts?.homePhone ?? '',
      additionalPhone: contacts?.additionalPhone ?? '',
    },
  });

  if (isLoading) return <PageLoader />;

  const onSubmit = async (data: FormData) => {
    const saved = await update({
      email: data.email,
      mobilePhone: data.mobilePhone ?? '',
      homePhone: data.homePhone || null,
      additionalPhone: data.additionalPhone || null,
    });
    reset({
      email: saved.email,
      mobilePhone: saved.mobilePhone,
      homePhone: saved.homePhone ?? '',
      additionalPhone: saved.additionalPhone ?? '',
    });
  };

  const inputClass = (hasError?: boolean) =>
    clsx(
      'w-full px-3.5 py-2.5 rounded-xl border text-sm outline-none transition-colors focus:ring-2 focus:ring-accent-500 focus:border-accent-500',
      hasError ? 'border-danger-500 bg-danger-50' : 'border-gray-300'
    );

  return (
    <div className="bg-white rounded-2xl shadow-card p-5">
      <div className="flex items-center gap-3 mb-5">
        <div className="w-10 h-10 rounded-xl bg-accent-50 flex items-center justify-center">
          <Mail className="w-5 h-5 text-accent-600" />
        </div>
        <div>
          <h2 className="text-lg font-semibold text-gray-900">Контакты</h2>
          <p className="text-sm text-gray-500">Email и телефоны для связи</p>
        </div>
      </div>

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1.5">Email</label>
          <input {...register('email')} type="email" className={inputClass(!!errors.email)} />
          {errors.email && <p className="mt-1 text-xs text-danger-600">{errors.email.message}</p>}
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">
              Мобильный телефон
            </label>
            <div className="relative">
              <Phone className="w-4 h-4 text-gray-400 absolute left-3 top-3" />
              <input {...register('mobilePhone')} className={clsx(inputClass(!!errors.mobilePhone), 'pl-9')} />
            </div>
            {errors.mobilePhone && (
              <p className="mt-1 text-xs text-danger-600">{errors.mobilePhone.message}</p>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">
              Домашний телефон
            </label>
            <input {...register('homePhone')} className={inputClass(!!errors.homePhone)} />
            {errors.homePhone && <p className="mt-1 text-xs text-danger-600">{errors.homePhone.message}</p>}
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1.5">
            Дополнительный телефон
          </label>
          <input {...register('additionalPhone')} className={inputClass(!!errors.additionalPhone)} />
          {errors.additionalPhone && (
            <p className="mt-1 text-xs text-danger-600">{errors.additionalPhone.message}</p>
          )}
        </div>

        {isSubmitSuccessful && (
          <p className="text-sm text-success-700 bg-success-50 border border-success-200 rounded-xl px-3 py-2">
            Контакты сохранены
          </p>
        )}

        <button
          type="submit"
          disabled={isPending}
          className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-primary-800 text-white text-sm font-medium hover:bg-primary-900 disabled:opacity-60"
        >
          {isPending ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
          Сохранить
        </button>
      </form>
    </div>
  );
}
