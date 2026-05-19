'use client';

import { useState, useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Loader2, Save } from 'lucide-react';
import { clsx } from 'clsx';
import { useAddresses, useUpdateAddress } from '@/lib/hooks/usePersonalData';
import { DataSourceBadge } from '@/components/personal-data/DataSourceBadge';
import { PageLoader } from '@/components/ui/LoadingSpinner';
import { ApiClientError } from '@/lib/api/client';
import type { EmployeeAddress } from '@corp-portal/shared-types';

const addressSchema = z.object({
  country: z.string().min(1, 'Укажите страну'),
  region: z.string().optional(),
  city: z.string().min(1, 'Укажите город'),
  street: z.string().optional(),
  house: z.string().optional(),
  apartment: z.string().optional(),
});

type AddressFormData = z.infer<typeof addressSchema>;

function AddressForm({
  title,
  address,
  type,
}: {
  title: string;
  address: EmployeeAddress | undefined;
  type: 'registration' | 'residence';
}) {
  const { mutateAsync: update, isPending } = useUpdateAddress();
  const [serverError, setServerError] = useState<string | null>(null);
  const [saved, setSaved] = useState(false);

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isDirty },
  } = useForm<AddressFormData>({
    resolver: zodResolver(addressSchema),
    values: {
      country: address?.country ?? '',
      region: address?.region ?? '',
      city: address?.city ?? '',
      street: address?.street ?? '',
      house: address?.house ?? '',
      apartment: address?.apartment ?? '',
    },
  });

  const onSubmit = async (data: AddressFormData) => {
    setServerError(null);
    try {
      await update({ type, data });
      setSaved(true);
      setTimeout(() => setSaved(false), 3000);
    } catch (err) {
      if (err instanceof ApiClientError) setServerError(err.message);
      else setServerError('Произошла ошибка. Попробуйте ещё раз.');
    }
  };

  return (
    <div className="bg-white rounded-2xl shadow-card p-5 space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-gray-900">{title}</h3>
        {address && <DataSourceBadge source={address.source} />}
      </div>

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-3">
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">
              Страна <span className="text-danger-500">*</span>
            </label>
            <input
              {...register('country')}
              placeholder="Казахстан"
              className={clsx(
                'w-full px-3.5 py-2.5 rounded-xl border text-sm outline-none focus:ring-2 focus:ring-accent-500 focus:border-accent-500',
                errors.country ? 'border-danger-500 bg-danger-50' : 'border-gray-300'
              )}
            />
            {errors.country && (
              <p className="mt-1 text-xs text-danger-600">{errors.country.message}</p>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">
              Регион / Область
            </label>
            <input
              {...register('region')}
              placeholder="Алматинская область"
              className="w-full px-3.5 py-2.5 rounded-xl border border-gray-300 text-sm outline-none focus:ring-2 focus:ring-accent-500 focus:border-accent-500"
            />
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1.5">
            Город / Населённый пункт <span className="text-danger-500">*</span>
          </label>
          <input
            {...register('city')}
            placeholder="Алматы"
            className={clsx(
              'w-full px-3.5 py-2.5 rounded-xl border text-sm outline-none focus:ring-2 focus:ring-accent-500 focus:border-accent-500',
              errors.city ? 'border-danger-500 bg-danger-50' : 'border-gray-300'
            )}
          />
          {errors.city && (
            <p className="mt-1 text-xs text-danger-600">{errors.city.message}</p>
          )}
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1.5">
            Улица
          </label>
          <input
            {...register('street')}
            placeholder="ул. Абая"
            className="w-full px-3.5 py-2.5 rounded-xl border border-gray-300 text-sm outline-none focus:ring-2 focus:ring-accent-500 focus:border-accent-500"
          />
        </div>

        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">Дом</label>
            <input
              {...register('house')}
              placeholder="12А"
              className="w-full px-3.5 py-2.5 rounded-xl border border-gray-300 text-sm outline-none focus:ring-2 focus:ring-accent-500 focus:border-accent-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">
              Квартира / Офис
            </label>
            <input
              {...register('apartment')}
              placeholder="45"
              className="w-full px-3.5 py-2.5 rounded-xl border border-gray-300 text-sm outline-none focus:ring-2 focus:ring-accent-500 focus:border-accent-500"
            />
          </div>
        </div>

        {serverError && (
          <div className="rounded-xl bg-danger-50 border border-danger-200 px-4 py-3">
            <p className="text-sm text-danger-700">{serverError}</p>
          </div>
        )}
        {saved && (
          <div className="rounded-xl bg-success-50 border border-success-200 px-4 py-3">
            <p className="text-sm text-success-700">Адрес сохранён успешно.</p>
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
  );
}

export default function AddressesPage() {
  const { data: addresses, isLoading } = useAddresses();
  const [sameAsRegistration, setSameAsRegistration] = useState(false);

  const regAddress = addresses?.find((a) => a.addressType === 'registration');
  const resAddress = addresses?.find((a) => a.addressType === 'residence');

  useEffect(() => {
    if (regAddress && resAddress) {
      setSameAsRegistration(
        regAddress.city === resAddress.city &&
          regAddress.street === resAddress.street &&
          regAddress.house === resAddress.house
      );
    }
  }, [regAddress, resAddress]);

  if (isLoading) return <PageLoader />;

  return (
    <div className="space-y-5">
      <h2 className="text-base font-semibold text-gray-900">Адреса</h2>
      <AddressForm title="Адрес регистрации (прописка)" address={regAddress} type="registration" />

      <div>
        <label className="flex items-center gap-2 px-1 mb-3 cursor-pointer">
          <input
            type="checkbox"
            checked={sameAsRegistration}
            onChange={(e) => setSameAsRegistration(e.target.checked)}
            className="w-4 h-4 rounded border-gray-300 text-primary-800 focus:ring-primary-800"
          />
          <span className="text-sm text-gray-700">Адрес проживания совпадает с адресом регистрации</span>
        </label>

        {!sameAsRegistration && (
          <AddressForm title="Адрес фактического проживания" address={resAddress} type="residence" />
        )}
      </div>
    </div>
  );
}
