'use client';

import { useRouter } from 'next/navigation';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { ChevronLeft, Thermometer, Loader2, AlertCircle } from 'lucide-react';
import { sickLeavesApi } from '@/lib/api/sickLeaves';
import clsx from 'clsx';

const schema = z.object({
  startDate: z.string().min(1, 'Выберите дату начала'),
  comment: z.string().optional(),
});

type FormData = z.infer<typeof schema>;

export default function NewSickLeavePage() {
  const router = useRouter();

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
    setError,
  } = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: {
      startDate: new Date().toISOString().split('T')[0],
    },
  });

  const onSubmit = async (data: FormData) => {
    try {
      await sickLeavesApi.create({
        startDate: data.startDate,
        comment: data.comment || undefined,
      });
      router.push('/sick-leaves');
    } catch (err) {
      setError('root', {
        message: err instanceof Error ? err.message : 'Произошла ошибка. Попробуйте снова.',
      });
    }
  };

  const today = new Date().toISOString().split('T')[0];

  return (
    <div className="max-w-lg mx-auto">
      {/* Header */}
      <div className="flex items-center gap-3 mb-6">
        <button
          onClick={() => router.back()}
          className="w-8 h-8 flex items-center justify-center rounded-xl hover:bg-gray-100 transition-colors"
        >
          <ChevronLeft className="w-5 h-5 text-gray-600" />
        </button>
        <div>
          <h1 className="text-xl font-bold text-gray-900">Открыть больничный</h1>
          <p className="text-sm text-gray-500">Регистрация больничного листа</p>
        </div>
      </div>

      {/* Info banner */}
      <div className="bg-warning-50 border border-warning-200 rounded-2xl px-5 py-4 flex items-start gap-3 mb-6">
        <AlertCircle className="w-5 h-5 text-warning-600 flex-shrink-0 mt-0.5" />
        <div>
          <p className="text-sm font-semibold text-warning-800">Важная информация</p>
          <p className="text-xs text-warning-700 mt-1 leading-relaxed">
            Открытый больничный будет активен до тех пор, пока вы или HR его не закроют.
            При закрытии необходимо указать дату окончания и номер больничного листа.
          </p>
        </div>
      </div>

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">
        {/* Start date */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1.5">
            Дата начала нетрудоспособности
          </label>
          <input
            {...register('startDate')}
            type="date"
            max={today}
            className={clsx(
              'w-full px-3.5 py-2.5 rounded-xl border text-sm outline-none transition-colors focus:ring-2 focus:ring-accent-500 focus:border-accent-500',
              errors.startDate ? 'border-danger-500 bg-danger-50' : 'border-gray-300'
            )}
          />
          {errors.startDate && (
            <p className="mt-1 text-xs text-danger-600">{errors.startDate.message}</p>
          )}
          <p className="mt-1.5 text-xs text-gray-400">
            Укажите дату, с которой вы не смогли приступить к работе
          </p>
        </div>

        {/* Comment */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1.5">
            Комментарий <span className="text-gray-400 font-normal">(необязательно)</span>
          </label>
          <textarea
            {...register('comment')}
            rows={3}
            placeholder="Дополнительные сведения…"
            className="w-full px-3.5 py-2.5 rounded-xl border border-gray-300 text-sm outline-none transition-colors focus:ring-2 focus:ring-accent-500 focus:border-accent-500 resize-none"
          />
        </div>

        {/* Root error */}
        {errors.root && (
          <div className="rounded-xl bg-danger-50 border border-danger-200 px-4 py-3">
            <p className="text-sm text-danger-700">{errors.root.message}</p>
          </div>
        )}

        {/* Confirmation note */}
        <div className="bg-gray-50 rounded-2xl px-4 py-3 text-xs text-gray-500 leading-relaxed">
          После регистрации больничный будет отображён в системе со статусом «Открыт».
          Ваш руководитель и HR получат уведомление.
        </div>

        {/* Actions */}
        <div className="flex gap-3 pt-2">
          <button
            type="button"
            onClick={() => router.back()}
            className="flex-1 px-4 py-2.5 rounded-xl border border-gray-200 text-sm font-medium text-gray-700 hover:bg-gray-50 transition-colors"
          >
            Отмена
          </button>
          <button
            type="submit"
            disabled={isSubmitting}
            className="flex-1 flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl bg-warning-600 text-white text-sm font-medium hover:bg-warning-700 transition-colors disabled:opacity-60"
          >
            {isSubmitting ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                Открытие…
              </>
            ) : (
              <>
                <Thermometer className="w-4 h-4" />
                Открыть больничный
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  );
}
