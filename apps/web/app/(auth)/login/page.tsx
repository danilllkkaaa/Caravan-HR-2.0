'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Eye, EyeOff, Loader2 } from 'lucide-react';
import { authApi } from '@/lib/api/auth';
import { useAuthStore } from '@corp-portal/ui-core';

const loginSchema = z.object({
  email: z
    .string()
    .trim()
    .toLowerCase()
    .min(1, 'Введите email')
    .max(320, 'Email слишком длинный')
    .email('Некорректный формат email'),
  password: z
    .string()
    .min(1, 'Введите пароль')
    .max(256, 'Пароль слишком длинный'),
});

type LoginFormData = z.infer<typeof loginSchema>;

export default function LoginPage() {
  const router = useRouter();
  const login = useAuthStore((s) => s.login);
  const [showPassword, setShowPassword] = useState(false);
  const [serverError, setServerError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema),
    defaultValues: { email: '', password: '' },
  });

  const onSubmit = async (data: LoginFormData) => {
    setServerError(null);
    try {
      const response = await authApi.login({
        email: data.email,
        password: data.password,
      });
      login(response.user, response.employee, response.accessToken);
      router.push('/');
      router.refresh();
    } catch (err) {
      if (err instanceof Error) {
        setServerError(err.message);
      } else {
        setServerError('Произошла ошибка. Попробуйте снова.');
      }
    }
  };

  return (
    <>
      <h2 className="text-xl font-semibold text-gray-900 mb-1">Вход в систему</h2>
      <p className="text-sm text-gray-500 mb-6">
        Введите корпоративный email и пароль
      </p>

      <form onSubmit={handleSubmit(onSubmit)} noValidate className="space-y-5">
        <div>
          <label
            htmlFor="email"
            className="block text-sm font-medium text-gray-700 mb-1.5"
          >
            Email
          </label>
          <input
            {...register('email')}
            id="email"
            type="email"
            autoComplete="email"
            autoCapitalize="none"
            autoCorrect="off"
            spellCheck={false}
            inputMode="email"
            enterKeyHint="next"
            autoFocus
            placeholder="ivanov@company.ru"
            aria-invalid={Boolean(errors.email)}
            aria-describedby={errors.email ? 'email-error' : undefined}
            className={`w-full px-3.5 py-2.5 rounded-xl border text-sm transition-colors outline-none
              focus:ring-2 focus:ring-accent-500 focus:border-accent-500
              ${errors.email
                ? 'border-danger-500 bg-danger-50 focus:ring-danger-500 focus:border-danger-500'
                : 'border-gray-300 bg-white hover:border-gray-400'
              }`}
          />
          {errors.email && (
            <p id="email-error" className="mt-1.5 text-xs text-danger-600">
              {errors.email.message}
            </p>
          )}
        </div>

        <div>
          <label
            htmlFor="password"
            className="block text-sm font-medium text-gray-700 mb-1.5"
          >
            Пароль
          </label>
          <div className="relative">
            <input
              {...register('password')}
              id="password"
              type={showPassword ? 'text' : 'password'}
              autoComplete="current-password"
              autoCapitalize="none"
              autoCorrect="off"
              spellCheck={false}
              enterKeyHint="done"
              placeholder="••••••••"
              aria-invalid={Boolean(errors.password)}
              aria-describedby={errors.password ? 'password-error' : undefined}
              className={`w-full px-3.5 py-2.5 pr-10 rounded-xl border text-sm transition-colors outline-none
                focus:ring-2 focus:ring-accent-500 focus:border-accent-500
                ${errors.password
                  ? 'border-danger-500 bg-danger-50 focus:ring-danger-500 focus:border-danger-500'
                  : 'border-gray-300 bg-white hover:border-gray-400'
                }`}
            />
            <button
              type="button"
              onClick={() => setShowPassword(!showPassword)}
              className="absolute right-1 top-1/2 -translate-y-1/2 w-9 h-9 flex items-center justify-center rounded-lg text-gray-400 hover:text-gray-600 hover:bg-gray-100 transition-colors"
              tabIndex={-1}
              aria-label={showPassword ? 'Скрыть пароль' : 'Показать пароль'}
            >
              {showPassword ? (
                <EyeOff className="w-4 h-4" />
              ) : (
                <Eye className="w-4 h-4" />
              )}
            </button>
          </div>
          {errors.password && (
            <p id="password-error" className="mt-1.5 text-xs text-danger-600">
              {errors.password.message}
            </p>
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
          className="w-full flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl
            bg-primary-800 hover:bg-primary-900 text-white text-sm font-medium
            transition-colors disabled:opacity-60 disabled:cursor-not-allowed
            focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-800"
        >
          {isSubmitting ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              Выполняется вход...
            </>
          ) : (
            'Войти'
          )}
        </button>
      </form>
    </>
  );
}
