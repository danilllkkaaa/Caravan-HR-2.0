'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { ChevronLeft, Loader2 } from 'lucide-react';
import { authApi } from '@/lib/api/auth';
import { ApiClientError } from '@/lib/api/client';
import { useAuthStore } from '@corp-portal/ui-core';

const schema = z
  .object({
    currentPassword: z.string().min(1, 'Введите текущий пароль'),
    newPassword: z.string().min(8, 'Новый пароль должен быть не короче 8 символов'),
    confirmPassword: z.string().min(1, 'Повторите новый пароль'),
  })
  .refine((data) => data.newPassword === data.confirmPassword, {
    path: ['confirmPassword'],
    message: 'Пароли не совпадают',
  });

type FormData = z.infer<typeof schema>;

export default function ChangePasswordPage() {
  const router = useRouter();
  const logout = useAuthStore((s) => s.logout);
  const [serverError, setServerError] = useState<string | null>(null);
  const [isDone, setIsDone] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: {
      currentPassword: '',
      newPassword: '',
      confirmPassword: '',
    },
  });

  const onSubmit = async (data: FormData) => {
    setServerError(null);
    try {
      await authApi.changePassword(data);
      logout();
      setIsDone(true);
    } catch (error) {
      if (error instanceof ApiClientError || error instanceof Error) {
        setServerError(error.message);
      } else {
        setServerError('Не удалось изменить пароль');
      }
    }
  };

  if (isDone) {
    return (
      <div className="max-w-lg mx-auto space-y-5">
        <h1 className="text-2xl font-bold text-gray-900">Пароль изменён</h1>
        <p className="text-sm text-gray-500">
          Все активные сессии завершены. Войдите снова с новым паролем.
        </p>
        <button
          type="button"
          onClick={() => router.push('/login')}
          className="w-full px-4 py-2.5 rounded-xl bg-primary-800 text-white text-sm font-medium hover:bg-primary-900 transition-colors"
        >
          Перейти ко входу
        </button>
      </div>
    );
  }

  return (
    <div className="max-w-lg mx-auto space-y-5">
      <div className="flex items-center gap-3">
        <button
          type="button"
          onClick={() => router.back()}
          className="w-8 h-8 flex items-center justify-center rounded-xl hover:bg-gray-100 transition-colors"
        >
          <ChevronLeft className="w-5 h-5 text-gray-600" />
        </button>
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Изменить пароль</h1>
          <p className="text-sm text-gray-500">После смены пароля потребуется новый вход</p>
        </div>
      </div>

      <form onSubmit={handleSubmit(onSubmit)} className="bg-white rounded-2xl shadow-card p-5 space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1.5">
            Текущий пароль
          </label>
          <input
            {...register('currentPassword')}
            type="password"
            autoComplete="current-password"
            className="w-full px-3.5 py-2.5 rounded-xl border border-gray-300 text-sm outline-none focus:ring-2 focus:ring-accent-500 focus:border-accent-500"
          />
          {errors.currentPassword && (
            <p className="mt-1 text-xs text-danger-600">{errors.currentPassword.message}</p>
          )}
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1.5">
            Новый пароль
          </label>
          <input
            {...register('newPassword')}
            type="password"
            autoComplete="new-password"
            className="w-full px-3.5 py-2.5 rounded-xl border border-gray-300 text-sm outline-none focus:ring-2 focus:ring-accent-500 focus:border-accent-500"
          />
          {errors.newPassword && (
            <p className="mt-1 text-xs text-danger-600">{errors.newPassword.message}</p>
          )}
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1.5">
            Повторите новый пароль
          </label>
          <input
            {...register('confirmPassword')}
            type="password"
            autoComplete="new-password"
            className="w-full px-3.5 py-2.5 rounded-xl border border-gray-300 text-sm outline-none focus:ring-2 focus:ring-accent-500 focus:border-accent-500"
          />
          {errors.confirmPassword && (
            <p className="mt-1 text-xs text-danger-600">{errors.confirmPassword.message}</p>
          )}
        </div>

        {serverError && (
          <div className="rounded-xl bg-danger-50 border border-danger-200 px-4 py-3">
            <p className="text-sm text-danger-700">{serverError}</p>
          </div>
        )}

        <button
          type="submit"
          disabled={isSubmitting}
          className="w-full flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl bg-primary-800 text-white text-sm font-medium hover:bg-primary-900 transition-colors disabled:opacity-60"
        >
          {isSubmitting && <Loader2 className="w-4 h-4 animate-spin" />}
          Изменить пароль
        </button>
      </form>
    </div>
  );
}
