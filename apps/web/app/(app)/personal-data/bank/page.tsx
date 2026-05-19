'use client';

import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Plus, Trash2, Building2, Loader2, Star, X } from 'lucide-react';
import { clsx } from 'clsx';
import { useBankAccounts, useAddBankAccount, useDeleteBankAccount } from '@/lib/hooks/usePersonalData';
import { DataSourceBadge } from '@/components/personal-data/DataSourceBadge';
import { DocumentUpload } from '@/components/personal-data/DocumentUpload';
import { PageLoader } from '@/components/ui/LoadingSpinner';
import { getBankUploadUrl } from '@/lib/api/personalData';
import { ApiClientError } from '@/lib/api/client';
import type { BankAccount } from '@corp-portal/shared-types';

const ACCOUNT_TYPE_LABELS: Record<BankAccount['accountType'], string> = {
  standard: 'Стандартный',
  social: 'Социальный',
  other: 'Другой',
};

const schema = z.object({
  bankName: z.string().min(1, 'Укажите название банка'),
  accountNumber: z.string().min(1, 'Укажите номер счёта'),
  bik: z.string().min(1, 'Укажите БИК банка'),
  accountType: z.enum(['standard', 'social', 'other']),
  holderName: z.string().min(1, 'Укажите имя держателя счёта'),
  isPrimary: z.boolean().optional(),
});

type FormData = z.infer<typeof schema>;

export default function BankPage() {
  const { data: accounts, isLoading } = useBankAccounts();
  const { mutateAsync: add, isPending: adding } = useAddBankAccount();
  const { mutateAsync: remove } = useDeleteBankAccount();

  const [showForm, setShowForm] = useState(false);
  const [documentKey, setDocumentKey] = useState<string | null>(null);
  const [serverError, setServerError] = useState<string | null>(null);
  const [deletingId, setDeletingId] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: { accountType: 'standard', isPrimary: false },
  });

  const onSubmit = async (data: FormData) => {
    setServerError(null);
    try {
      await add({
        bankName: data.bankName,
        accountNumber: data.accountNumber,
        bik: data.bik,
        accountType: data.accountType,
        holderName: data.holderName,
        documentUrl: documentKey,
        isPrimary: data.isPrimary ?? false,
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
        <h2 className="text-base font-semibold text-gray-900">Банковские реквизиты</h2>
        <button
          onClick={() => setShowForm(!showForm)}
          className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-primary-800 text-white text-sm font-medium hover:bg-primary-900 transition-colors"
        >
          <Plus className="w-4 h-4" />
          Добавить
        </button>
      </div>

      {accounts?.length === 0 && !showForm && (
        <div className="bg-white rounded-2xl shadow-card p-8 text-center">
          <Building2 className="w-8 h-8 text-gray-300 mx-auto mb-3" />
          <p className="text-sm font-medium text-gray-900 mb-1">Банковские счета не добавлены</p>
          <p className="text-xs text-gray-400 mb-4">Добавьте реквизиты для получения выплат</p>
          <button
            onClick={() => setShowForm(true)}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-primary-800 text-white text-sm font-medium hover:bg-primary-900 transition-colors"
          >
            <Plus className="w-4 h-4" />
            Добавить счёт
          </button>
        </div>
      )}

      <div className="space-y-3">
        {accounts?.map((account) => (
          <div key={account.id} className="bg-white rounded-2xl shadow-card p-4">
            <div className="flex items-start justify-between gap-3">
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 flex-wrap mb-1">
                  <p className="text-sm font-semibold text-gray-900">{account.bankName}</p>
                  {account.isPrimary && (
                    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-accent-100 text-accent-700 border border-accent-200">
                      <Star className="w-3 h-3" />
                      Основной
                    </span>
                  )}
                  <DataSourceBadge source={account.source} />
                </div>
                <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-xs text-gray-500 mt-1">
                  <div>
                    <span className="text-gray-400">Счёт: </span>
                    <span className="text-gray-700 font-medium font-mono">{account.accountNumber}</span>
                  </div>
                  <div>
                    <span className="text-gray-400">БИК: </span>
                    <span className="text-gray-700">{account.bik}</span>
                  </div>
                  <div>
                    <span className="text-gray-400">Тип: </span>
                    <span className="text-gray-700">{ACCOUNT_TYPE_LABELS[account.accountType]}</span>
                  </div>
                  <div>
                    <span className="text-gray-400">Держатель: </span>
                    <span className="text-gray-700 truncate">{account.holderName}</span>
                  </div>
                </div>
              </div>
              <button
                onClick={() => void handleDelete(account.id)}
                disabled={deletingId === account.id}
                className="p-2 rounded-xl hover:bg-danger-50 transition-colors flex-shrink-0"
              >
                {deletingId === account.id ? (
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
        <div className="bg-white rounded-2xl shadow-card p-5 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold text-gray-900">Новый банковский счёт</h3>
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
                Банк <span className="text-danger-500">*</span>
              </label>
              <input
                {...register('bankName')}
                placeholder="АО «Народный Банк Казахстана»"
                className={clsx(
                  'w-full px-3.5 py-2.5 rounded-xl border text-sm outline-none focus:ring-2 focus:ring-accent-500 focus:border-accent-500',
                  errors.bankName ? 'border-danger-500 bg-danger-50' : 'border-gray-300'
                )}
              />
              {errors.bankName && (
                <p className="mt-1 text-xs text-danger-600">{errors.bankName.message}</p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">
                Номер счёта / IBAN <span className="text-danger-500">*</span>
              </label>
              <input
                {...register('accountNumber')}
                placeholder="KZ00000000000000000"
                className={clsx(
                  'w-full px-3.5 py-2.5 rounded-xl border text-sm font-mono outline-none focus:ring-2 focus:ring-accent-500 focus:border-accent-500',
                  errors.accountNumber ? 'border-danger-500 bg-danger-50' : 'border-gray-300'
                )}
              />
              {errors.accountNumber && (
                <p className="mt-1 text-xs text-danger-600">{errors.accountNumber.message}</p>
              )}
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1.5">
                  БИК <span className="text-danger-500">*</span>
                </label>
                <input
                  {...register('bik')}
                  placeholder="HSBKKZKX"
                  className={clsx(
                    'w-full px-3.5 py-2.5 rounded-xl border text-sm outline-none focus:ring-2 focus:ring-accent-500 focus:border-accent-500',
                    errors.bik ? 'border-danger-500 bg-danger-50' : 'border-gray-300'
                  )}
                />
                {errors.bik && (
                  <p className="mt-1 text-xs text-danger-600">{errors.bik.message}</p>
                )}
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1.5">
                  Тип счёта <span className="text-danger-500">*</span>
                </label>
                <select
                  {...register('accountType')}
                  className="w-full px-3.5 py-2.5 rounded-xl border border-gray-300 text-sm outline-none focus:ring-2 focus:ring-accent-500 focus:border-accent-500 bg-white"
                >
                  {Object.entries(ACCOUNT_TYPE_LABELS).map(([val, label]) => (
                    <option key={val} value={val}>{label}</option>
                  ))}
                </select>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">
                Имя держателя счёта <span className="text-danger-500">*</span>
              </label>
              <input
                {...register('holderName')}
                placeholder="IVAN IVANOV"
                className={clsx(
                  'w-full px-3.5 py-2.5 rounded-xl border text-sm outline-none focus:ring-2 focus:ring-accent-500 focus:border-accent-500',
                  errors.holderName ? 'border-danger-500 bg-danger-50' : 'border-gray-300'
                )}
              />
              {errors.holderName && (
                <p className="mt-1 text-xs text-danger-600">{errors.holderName.message}</p>
              )}
            </div>

            <label className="flex items-center gap-2 cursor-pointer">
              <input
                {...register('isPrimary')}
                type="checkbox"
                className="w-4 h-4 rounded border-gray-300 text-primary-800 focus:ring-primary-800"
              />
              <span className="text-sm text-gray-700">Сделать основным счётом</span>
            </label>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">
                Подтверждающий документ
              </label>
              <DocumentUpload
                getUploadUrl={getBankUploadUrl}
                onUploaded={(key) => setDocumentKey(key)}
              />
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
