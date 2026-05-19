'use client';

import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Plus, Trash2, Users, Loader2, X, Baby } from 'lucide-react';
import { clsx } from 'clsx';
import { useFamily, useAddFamilyMember, useDeleteFamilyMember } from '@/lib/hooks/usePersonalData';
import { DataSourceBadge } from '@/components/personal-data/DataSourceBadge';
import { DocumentUpload } from '@/components/personal-data/DocumentUpload';
import { PageLoader } from '@/components/ui/LoadingSpinner';
import { getDocumentUploadUrl } from '@/lib/api/personalData';
import { ApiClientError } from '@/lib/api/client';

const childSchema = z.object({
  firstName: z.string().min(1, 'Введите имя'),
  lastName: z.string().min(1, 'Введите фамилию'),
  middleName: z.string().optional(),
  birthDate: z.string().optional(),
  iin: z.string().optional(),
  birthCertNumber: z.string().optional(),
  birthCertSeries: z.string().optional(),
  birthCertIssueDate: z.string().optional(),
  birthCertIssuedBy: z.string().optional(),
});

type ChildFormData = z.infer<typeof childSchema>;

const spouseSchema = z.object({
  firstName: z.string().min(1, 'Введите имя'),
  lastName: z.string().min(1, 'Введите фамилию'),
  middleName: z.string().optional(),
  birthDate: z.string().optional(),
  iin: z.string().optional(),
  marriageCertNumber: z.string().optional(),
  marriageCertIssueDate: z.string().optional(),
  marriageCertOrg: z.string().optional(),
});

type SpouseFormData = z.infer<typeof spouseSchema>;

export default function FamilyPage() {
  const { data: family, isLoading } = useFamily();
  const { mutateAsync: add, isPending: adding } = useAddFamilyMember();
  const { mutateAsync: remove, isPending: removing } = useDeleteFamilyMember();

  const [showChildForm, setShowChildForm] = useState(false);
  const [showSpouseForm, setShowSpouseForm] = useState(false);
  const [childDocKey, setChildDocKey] = useState<string | null>(null);
  const [spouseDocKey, setSpouseDocKey] = useState<string | null>(null);
  const [serverError, setServerError] = useState<string | null>(null);
  const [deletingId, setDeletingId] = useState<string | null>(null);

  const childForm = useForm<ChildFormData>({ resolver: zodResolver(childSchema) });
  const spouseForm = useForm<SpouseFormData>({ resolver: zodResolver(spouseSchema) });

  const spouseRecord = family?.find((m) => m.memberType === 'spouse');
  const children = family?.filter((m) => m.memberType === 'child') ?? [];

  const handleAddChild = async (data: ChildFormData) => {
    setServerError(null);
    try {
      await add({
        memberType: 'child',
        firstName: data.firstName,
        lastName: data.lastName,
        middleName: data.middleName ?? null,
        birthDate: data.birthDate ?? null,
        iin: data.iin ?? null,
        birthCertNumber: data.birthCertNumber ?? null,
        birthCertSeries: data.birthCertSeries ?? null,
        birthCertIssueDate: data.birthCertIssueDate ?? null,
        birthCertIssuedBy: data.birthCertIssuedBy ?? null,
        spouseStatus: null,
        marriageCertNumber: null,
        marriageCertIssueDate: null,
        marriageCertOrg: null,
        documentUrl: childDocKey,
      });
      childForm.reset();
      setChildDocKey(null);
      setShowChildForm(false);
    } catch (err) {
      if (err instanceof ApiClientError) setServerError(err.message);
      else setServerError('Произошла ошибка.');
    }
  };

  const handleAddSpouse = async (data: SpouseFormData) => {
    setServerError(null);
    try {
      await add({
        memberType: 'spouse',
        firstName: data.firstName,
        lastName: data.lastName,
        middleName: data.middleName ?? null,
        birthDate: data.birthDate ?? null,
        iin: data.iin ?? null,
        birthCertNumber: null,
        birthCertSeries: null,
        birthCertIssueDate: null,
        birthCertIssuedBy: null,
        spouseStatus: 'active',
        marriageCertNumber: data.marriageCertNumber ?? null,
        marriageCertIssueDate: data.marriageCertIssueDate ?? null,
        marriageCertOrg: data.marriageCertOrg ?? null,
        documentUrl: spouseDocKey,
      });
      spouseForm.reset();
      setSpouseDocKey(null);
      setShowSpouseForm(false);
    } catch (err) {
      if (err instanceof ApiClientError) setServerError(err.message);
      else setServerError('Произошла ошибка.');
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
    <div className="space-y-5">
      <h2 className="text-base font-semibold text-gray-900">Семья</h2>

      {/* Spouse section */}
      <div className="bg-white rounded-2xl shadow-card overflow-hidden">
        <div className="flex items-center justify-between px-5 py-3 border-b border-gray-50">
          <h3 className="text-sm font-semibold text-gray-700">Супруг(а)</h3>
          {!spouseRecord && !showSpouseForm && (
            <button
              onClick={() => setShowSpouseForm(true)}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-gray-100 text-gray-700 text-xs font-medium hover:bg-gray-200 transition-colors"
            >
              <Plus className="w-3.5 h-3.5" />
              Добавить
            </button>
          )}
        </div>

        {spouseRecord ? (
          <div className="px-5 py-4">
            <div className="flex items-start justify-between gap-3">
              <div>
                <div className="flex items-center gap-2 mb-1">
                  <p className="text-sm font-semibold text-gray-900">
                    {spouseRecord.lastName} {spouseRecord.firstName} {spouseRecord.middleName ?? ''}
                  </p>
                  <DataSourceBadge source={spouseRecord.source} />
                </div>
                {spouseRecord.birthDate && (
                  <p className="text-xs text-gray-500">
                    Дата рождения: {new Date(spouseRecord.birthDate).toLocaleDateString('ru-RU')}
                  </p>
                )}
                {spouseRecord.iin && (
                  <p className="text-xs text-gray-500">ИИН: {spouseRecord.iin}</p>
                )}
                {spouseRecord.marriageCertNumber && (
                  <p className="text-xs text-gray-500">
                    Свидетельство о браке: {spouseRecord.marriageCertNumber}
                  </p>
                )}
              </div>
              {spouseRecord.source === 'user' && (
                <button
                  onClick={() => void handleDelete(spouseRecord.id)}
                  disabled={deletingId === spouseRecord.id}
                  className="p-2 rounded-xl hover:bg-danger-50 transition-colors"
                >
                  {deletingId === spouseRecord.id ? (
                    <Loader2 className="w-4 h-4 animate-spin text-gray-400" />
                  ) : (
                    <Trash2 className="w-4 h-4 text-gray-400 hover:text-danger-600" />
                  )}
                </button>
              )}
            </div>
          </div>
        ) : showSpouseForm ? (
          <div className="px-5 py-4 space-y-4">
            <form onSubmit={spouseForm.handleSubmit(handleAddSpouse)} className="space-y-3">
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1.5">
                    Фамилия <span className="text-danger-500">*</span>
                  </label>
                  <input
                    {...spouseForm.register('lastName')}
                    placeholder="Сейткалиева"
                    className={clsx(
                      'w-full px-3.5 py-2.5 rounded-xl border text-sm outline-none focus:ring-2 focus:ring-accent-500 focus:border-accent-500',
                      spouseForm.formState.errors.lastName ? 'border-danger-500 bg-danger-50' : 'border-gray-300'
                    )}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1.5">
                    Имя <span className="text-danger-500">*</span>
                  </label>
                  <input
                    {...spouseForm.register('firstName')}
                    placeholder="Айгерим"
                    className={clsx(
                      'w-full px-3.5 py-2.5 rounded-xl border text-sm outline-none focus:ring-2 focus:ring-accent-500 focus:border-accent-500',
                      spouseForm.formState.errors.firstName ? 'border-danger-500 bg-danger-50' : 'border-gray-300'
                    )}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1.5">Отчество</label>
                  <input
                    {...spouseForm.register('middleName')}
                    className="w-full px-3.5 py-2.5 rounded-xl border border-gray-300 text-sm outline-none focus:ring-2 focus:ring-accent-500 focus:border-accent-500"
                  />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1.5">Дата рождения</label>
                  <input
                    {...spouseForm.register('birthDate')}
                    type="date"
                    className="w-full px-3.5 py-2.5 rounded-xl border border-gray-300 text-sm outline-none focus:ring-2 focus:ring-accent-500 focus:border-accent-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1.5">ИИН</label>
                  <input
                    {...spouseForm.register('iin')}
                    className="w-full px-3.5 py-2.5 rounded-xl border border-gray-300 text-sm outline-none focus:ring-2 focus:ring-accent-500 focus:border-accent-500"
                  />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1.5">
                    Номер свидетельства о браке
                  </label>
                  <input
                    {...spouseForm.register('marriageCertNumber')}
                    className="w-full px-3.5 py-2.5 rounded-xl border border-gray-300 text-sm outline-none focus:ring-2 focus:ring-accent-500 focus:border-accent-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1.5">Дата регистрации</label>
                  <input
                    {...spouseForm.register('marriageCertIssueDate')}
                    type="date"
                    className="w-full px-3.5 py-2.5 rounded-xl border border-gray-300 text-sm outline-none focus:ring-2 focus:ring-accent-500 focus:border-accent-500"
                  />
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1.5">
                  Орган выдачи свидетельства
                </label>
                <input
                  {...spouseForm.register('marriageCertOrg')}
                  placeholder="РАГС г. Алматы"
                  className="w-full px-3.5 py-2.5 rounded-xl border border-gray-300 text-sm outline-none focus:ring-2 focus:ring-accent-500 focus:border-accent-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1.5">
                  Скан свидетельства о браке
                </label>
                <DocumentUpload
                  getUploadUrl={getDocumentUploadUrl}
                  onUploaded={(key) => setSpouseDocKey(key)}
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
                    setShowSpouseForm(false);
                    spouseForm.reset();
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
        ) : (
          <div className="px-5 py-4 text-sm text-gray-400">Не указан</div>
        )}
      </div>

      {/* Children section */}
      <div className="bg-white rounded-2xl shadow-card overflow-hidden">
        <div className="flex items-center justify-between px-5 py-3 border-b border-gray-50">
          <h3 className="text-sm font-semibold text-gray-700">
            Дети {children.length > 0 && `(${children.length})`}
          </h3>
          <button
            onClick={() => setShowChildForm(!showChildForm)}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-gray-100 text-gray-700 text-xs font-medium hover:bg-gray-200 transition-colors"
          >
            <Plus className="w-3.5 h-3.5" />
            Добавить ребёнка
          </button>
        </div>

        {children.length === 0 && !showChildForm && (
          <div className="px-5 py-4 text-center">
            <Baby className="w-6 h-6 text-gray-300 mx-auto mb-2" />
            <p className="text-sm text-gray-400">Дети не добавлены</p>
          </div>
        )}

        <div className="divide-y divide-gray-50">
          {children.map((child) => (
            <div key={child.id} className="flex items-start justify-between gap-3 px-5 py-4">
              <div>
                <div className="flex items-center gap-2 mb-1">
                  <p className="text-sm font-semibold text-gray-900">
                    {child.lastName} {child.firstName} {child.middleName ?? ''}
                  </p>
                  <DataSourceBadge source={child.source} />
                </div>
                {child.birthDate && (
                  <p className="text-xs text-gray-500">
                    Дата рождения: {new Date(child.birthDate).toLocaleDateString('ru-RU')}
                  </p>
                )}
                {child.iin && <p className="text-xs text-gray-500">ИИН: {child.iin}</p>}
                {child.birthCertNumber && (
                  <p className="text-xs text-gray-500">
                    Свидетельство: {child.birthCertSeries ?? ''} {child.birthCertNumber}
                  </p>
                )}
              </div>
              {child.source === 'user' && (
                <button
                  onClick={() => void handleDelete(child.id)}
                  disabled={deletingId === child.id}
                  className="p-2 rounded-xl hover:bg-danger-50 transition-colors"
                >
                  {deletingId === child.id ? (
                    <Loader2 className="w-4 h-4 animate-spin text-gray-400" />
                  ) : (
                    <Trash2 className="w-4 h-4 text-gray-400 hover:text-danger-600" />
                  )}
                </button>
              )}
            </div>
          ))}
        </div>

        {showChildForm && (
          <div className="px-5 py-4 border-t border-gray-100 space-y-4">
            <div className="flex items-center justify-between">
              <p className="text-sm font-semibold text-gray-900">Новый ребёнок</p>
              <button
                onClick={() => {
                  setShowChildForm(false);
                  childForm.reset();
                }}
                className="p-1.5 rounded-xl hover:bg-gray-100 transition-colors"
              >
                <X className="w-4 h-4 text-gray-500" />
              </button>
            </div>
            <form onSubmit={childForm.handleSubmit(handleAddChild)} className="space-y-3">
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1.5">
                    Фамилия <span className="text-danger-500">*</span>
                  </label>
                  <input
                    {...childForm.register('lastName')}
                    className={clsx(
                      'w-full px-3.5 py-2.5 rounded-xl border text-sm outline-none focus:ring-2 focus:ring-accent-500 focus:border-accent-500',
                      childForm.formState.errors.lastName ? 'border-danger-500 bg-danger-50' : 'border-gray-300'
                    )}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1.5">
                    Имя <span className="text-danger-500">*</span>
                  </label>
                  <input
                    {...childForm.register('firstName')}
                    className={clsx(
                      'w-full px-3.5 py-2.5 rounded-xl border text-sm outline-none focus:ring-2 focus:ring-accent-500 focus:border-accent-500',
                      childForm.formState.errors.firstName ? 'border-danger-500 bg-danger-50' : 'border-gray-300'
                    )}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1.5">Отчество</label>
                  <input
                    {...childForm.register('middleName')}
                    className="w-full px-3.5 py-2.5 rounded-xl border border-gray-300 text-sm outline-none focus:ring-2 focus:ring-accent-500 focus:border-accent-500"
                  />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1.5">Дата рождения</label>
                  <input
                    {...childForm.register('birthDate')}
                    type="date"
                    className="w-full px-3.5 py-2.5 rounded-xl border border-gray-300 text-sm outline-none focus:ring-2 focus:ring-accent-500 focus:border-accent-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1.5">ИИН</label>
                  <input
                    {...childForm.register('iin')}
                    className="w-full px-3.5 py-2.5 rounded-xl border border-gray-300 text-sm outline-none focus:ring-2 focus:ring-accent-500 focus:border-accent-500"
                  />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1.5">Серия св-ва о рождении</label>
                  <input
                    {...childForm.register('birthCertSeries')}
                    className="w-full px-3.5 py-2.5 rounded-xl border border-gray-300 text-sm outline-none focus:ring-2 focus:ring-accent-500 focus:border-accent-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1.5">Номер св-ва о рождении</label>
                  <input
                    {...childForm.register('birthCertNumber')}
                    className="w-full px-3.5 py-2.5 rounded-xl border border-gray-300 text-sm outline-none focus:ring-2 focus:ring-accent-500 focus:border-accent-500"
                  />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1.5">Дата выдачи</label>
                  <input
                    {...childForm.register('birthCertIssueDate')}
                    type="date"
                    className="w-full px-3.5 py-2.5 rounded-xl border border-gray-300 text-sm outline-none focus:ring-2 focus:ring-accent-500 focus:border-accent-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1.5">Кем выдано</label>
                  <input
                    {...childForm.register('birthCertIssuedBy')}
                    className="w-full px-3.5 py-2.5 rounded-xl border border-gray-300 text-sm outline-none focus:ring-2 focus:ring-accent-500 focus:border-accent-500"
                  />
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1.5">
                  Скан свидетельства о рождении
                </label>
                <DocumentUpload
                  getUploadUrl={getDocumentUploadUrl}
                  onUploaded={(key) => setChildDocKey(key)}
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
                    setShowChildForm(false);
                    childForm.reset();
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
    </div>
  );
}
