'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useForm, Controller } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { ChevronLeft, ChevronRight, Check, Loader2 } from 'lucide-react';
import { useVacationTypes, useVacationBalance } from '@/lib/hooks/useVacations';
import { ApiClientError } from '@/lib/api/client';
import { vacationsApi } from '@/lib/api/vacations';
import { calculateWorkdays, calculateCalendarDays, formatDateRangeRu, formatDateRu } from '@corp-portal/ui-core';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import clsx from 'clsx';

const schema = z
  .object({
    vacationTypeId: z.string().min(1, 'Выберите тип отпуска'),
    startDate: z.string().min(1, 'Выберите дату начала'),
    endDate: z.string().min(1, 'Выберите дату окончания'),
    comment: z.string().optional(),
  })
  .refine((d) => new Date(d.endDate) >= new Date(d.startDate), {
    message: 'Дата окончания должна быть не раньше даты начала',
    path: ['endDate'],
  });

type FormData = z.infer<typeof schema>;

const STEPS = ['Тип отпуска', 'Даты', 'Просмотр', 'Подтверждение'];
const Cl = 'section' as const;

function StepIndicator({ current, total }: { current: number; total: number }) {
  return (
    <div className="flex items-center gap-2 mb-6">
      {Array.from({ length: total }).map((_, i) => (
        <div key={i} className="flex items-center gap-2">
          <div
            className={clsx(
              'w-8 h-8 rounded-full flex items-center justify-center text-sm font-semibold transition-colors',
              i < current
                ? 'bg-success-500 text-white'
                : i === current
                ? 'bg-primary-800 text-white'
                : 'bg-gray-100 text-gray-400'
            )}
          >
            {i < current ? <Check className="w-4 h-4" /> : i + 1}
          </div>
          {i < total - 1 && (
            <div
              className={clsx(
                'h-0.5 w-8 sm:w-12 transition-colors',
                i < current ? 'bg-success-500' : 'bg-gray-200'
              )}
            />
          )}
        </div>
      ))}
    </div>
  );
}

export default function NewVacationPage() {
  const router = useRouter();
  const [step, setStep] = useState(0);
  const [serverError, setServerError] = useState<string | null>(null);

  const { data: types, isLoading: typesLoading } = useVacationTypes();

  const {
    control,
    register,
    watch,
    handleSubmit,
    formState: { errors, isSubmitting },
    trigger,
  } = useForm<FormData>({
    resolver: zodResolver(schema),
    mode: 'onChange',
  });

  const watchedTypeId = watch('vacationTypeId');
  const watchedStart = watch('startDate');
  const watchedEnd = watch('endDate');

  const selectedType = types?.find((t) => t.id === watchedTypeId);
  const { data: balance } = useVacationBalance(
    watchedStart ? new Date(watchedStart).getFullYear() : undefined
  );

  const workdays =
    watchedStart && watchedEnd
      ? calculateWorkdays(watchedStart, watchedEnd)
      : 0;

  const calendarDays =
    watchedStart && watchedEnd
      ? calculateCalendarDays(watchedStart, watchedEnd)
      : 0;

  const goNext = async () => {
    let valid = false;
    if (step === 0) valid = await trigger('vacationTypeId');
    if (step === 1) valid = await trigger(['startDate', 'endDate']);
    if (step === 2) { setStep(3); return; }
    if (valid) setStep((s) => s + 1);
  };

  const onSubmit = async (data: FormData) => {
    setServerError(null);
    try {
      const created = await vacationsApi.create({
        vacationTypeId: data.vacationTypeId,
        startDate: data.startDate,
        endDate: data.endDate,
        comment: data.comment || undefined,
        submit: true,
      });
      if (created.warnings?.short_notice) {
        // shown on list; non-blocking per TZ
      }
      router.push('/vacations');
    } catch (err) {
      if (err instanceof ApiClientError) {
        setServerError(err.message);
      } else {
        setServerError(err instanceof Error ? err.message : 'Произошла ошибка');
      }
    }
  };

  const today = new Date().toISOString().split('T')[0];

  return (
    <div className="max-w-lg mx-auto">
      {/* Header */}
      <div className="flex items-center gap-3 mb-6">
        <button
          onClick={() => (step === 0 ? router.back() : setStep((s) => s - 1))}
          className="w-8 h-8 flex items-center justify-center rounded-xl hover:bg-gray-100 transition-colors"
        >
          <ChevronLeft className="w-5 h-5 text-gray-600" />
        </button>
        <div>
          <h1 className="text-xl font-bold text-gray-900">Новый отпуск</h1>
          <p className="text-sm text-gray-500">Шаг {step + 1} из {STEPS.length}</p>
        </div>
      </div>

      <StepIndicator current={step} total={STEPS.length} />

      <form onSubmit={handleSubmit(onSubmit)}>
        {/* Step 1: Type selection */}
        {step === 0 && (
          <div className="space-y-4">
            <h2 className="text-lg font-semibold text-gray-900">Тип отпуска</h2>
            <p className="text-sm text-gray-500">Выберите вид отпуска из доступных вариантов</p>

            {typesLoading ? (
              <div className="flex justify-center py-8">
                <LoadingSpinner size="lg" />
              </div>
            ) : (
              <Controller
                name="vacationTypeId"
                control={control}
                render={({ field }) => (
                  <div className="space-y-2">
                    {types?.map((type) => (
                      <button
                        key={type.id}
                        type="button"
                        onClick={() => field.onChange(type.id)}
                        className={clsx(
                          'w-full text-left p-4 rounded-2xl border-2 transition-all',
                          field.value === type.id
                            ? 'border-primary-800 bg-primary-50'
                            : 'border-gray-200 bg-white hover:border-gray-300'
                        )}
                      >
                        <div className="flex items-start justify-between">
                          <div>
                            <p className="font-semibold text-gray-900">{type.name}</p>
                          </div>
                          <div className="flex flex-col items-end gap-1 ml-3">
                            {type.isPaid && (
                              <span className="text-xs bg-success-100 text-success-700 px-2 py-0.5 rounded-full font-medium">
                                Оплачиваемый
                              </span>
                            )}
                            {type.requiresDocuments && (
                              <span className="text-xs text-gray-400">нужны документы</span>
                            )}
                          </div>
                        </div>
                        {field.value === type.id && (
                          <div className="mt-2 flex items-center gap-1 text-primary-700 text-xs font-medium">
                            <Check className="w-3.5 h-3.5" />
                            Выбрано
                          </div>
                        )}
                      </button>
                    ))}
                  </div>
                )}
              />
            )}
            {errors.vacationTypeId && (
              <p className="text-xs text-danger-600">{errors.vacationTypeId.message}</p>
            )}
          </div>
        )}

        {/* Step 2: Date picker */}
        {step === 1 && (
          <div className="space-y-5">
            <div>
              <h2 className="text-lg font-semibold text-gray-900">Даты отпуска</h2>
              <p className="text-sm text-gray-500 mt-0.5">
                {selectedType?.name} · Выберите период
              </p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">
                Дата начала
              </label>
              <input
                {...register('startDate')}
                type="date"
                min={today}
                className={clsx(
                  'w-full px-3.5 py-2.5 rounded-xl border text-sm outline-none transition-colors focus:ring-2 focus:ring-accent-500 focus:border-accent-500',
                  errors.startDate ? 'border-danger-500 bg-danger-50' : 'border-gray-300'
                )}
              />
              {errors.startDate && (
                <p className="mt-1 text-xs text-danger-600">{errors.startDate.message}</p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">
                Дата окончания
              </label>
              <input
                {...register('endDate')}
                type="date"
                min={watchedStart || today}
                className={clsx(
                  'w-full px-3.5 py-2.5 rounded-xl border text-sm outline-none transition-colors focus:ring-2 focus:ring-accent-500 focus:border-accent-500',
                  errors.endDate ? 'border-danger-500 bg-danger-50' : 'border-gray-300'
                )}
              />
              {errors.endDate && (
                <p className="mt-1 text-xs text-danger-600">{errors.endDate.message}</p>
              )}
            </div>

            {watchedStart && watchedEnd && workdays > 0 && (
              <div className="bg-accent-50 rounded-2xl p-4 space-y-2">
                <p className="text-sm font-semibold text-accent-900">
                  {formatDateRangeRu(watchedStart, watchedEnd)}
                </p>
                <div className="flex gap-4 text-sm">
                  <div>
                    <span className="text-gray-500">Рабочих: </span>
                    <span className="font-semibold text-gray-900">{workdays} дн.</span>
                  </div>
                  <div>
                    <span className="text-gray-500">Календарных: </span>
                    <span className="font-semibold text-gray-900">{calendarDays} дн.</span>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Step 3: Preview */}
        {step === 2 && (
          <div className="space-y-5">
            <h2 className="text-lg font-semibold text-gray-900">Просмотр заявки</h2>

            <div className="bg-white rounded-2xl shadow-card divide-y divide-gray-50">
              <div className="flex justify-between px-5 py-4">
                <span className="text-sm text-gray-500">Тип отпуска</span>
                <span className="text-sm font-semibold text-gray-900">{selectedType?.name}</span>
              </div>
              <div className="flex justify-between px-5 py-4">
                <span className="text-sm text-gray-500">Период</span>
                <span className="text-sm font-semibold text-gray-900">
                  {watchedStart && watchedEnd ? formatDateRangeRu(watchedStart, watchedEnd) : '—'}
                </span>
              </div>
              <div className="flex justify-between px-5 py-4">
                <span className="text-sm text-gray-500">Рабочих дней</span>
                <span className="text-sm font-semibold text-gray-900">{workdays}</span>
              </div>
              <div className="flex justify-between px-5 py-4">
                <span className="text-sm text-gray-500">Календарных дней</span>
                <span className="text-sm font-semibold text-gray-900">{calendarDays}</span>
              </div>
              {balance && (
                <Cl className="flex justify-between px-5 py-4 bg-accent-50/50">
                  <span className="text-sm text-gray-500">Остаток отпуска</span>
                  <span className="text-sm font-semibold text-gray-900">
                    {balance.availableDays} из {balance.totalDays} дн.
                  </span>
                </Cl>
              )}
            </div>

            <p className="text-xs text-gray-400 text-center">
              Расчёт дней предварительный и не учитывает праздничные дни.
              Точный расчёт будет выполнен после утверждения заявки.
            </p>
          </div>
        )}

        {/* Step 4: Comment + Confirmation */}
        {step === 3 && (
          <div className="space-y-5">
            <div>
              <h2 className="text-lg font-semibold text-gray-900">Комментарий и подтверждение</h2>
              <p className="text-sm text-gray-500 mt-0.5">Добавьте комментарий (необязательно) и подтвердите заявку</p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">
                Комментарий
              </label>
              <textarea
                {...register('comment')}
                rows={3}
                placeholder="Например: прошу согласовать отпуск в связи с семейными обстоятельствами"
                className="w-full px-3.5 py-2.5 rounded-xl border border-gray-300 text-sm outline-none transition-colors focus:ring-2 focus:ring-accent-500 focus:border-accent-500 resize-none"
              />
            </div>

            {serverError && (
              <div className="rounded-xl bg-danger-50 border border-danger-200 px-4 py-3">
                <p className="text-sm text-danger-700">{serverError}</p>
              </div>
            )}

            <div className="bg-primary-50 rounded-2xl p-4 text-sm text-primary-800">
              Отправляя заявку, вы подтверждаете корректность указанных дат.
              Заявка будет направлена на согласование руководителю.
            </div>
          </div>
        )}

        {/* Navigation buttons */}
        <div className="flex gap-3 mt-8">
          {step > 0 && (
            <button
              type="button"
              onClick={() => setStep((s) => s - 1)}
              className="flex-1 px-4 py-2.5 rounded-xl border border-gray-200 text-sm font-medium text-gray-700 hover:bg-gray-50 transition-colors"
            >
              Назад
            </button>
          )}
          {step < STEPS.length - 1 ? (
            <button
              type="button"
              onClick={goNext}
              className="flex-1 flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl bg-primary-800 text-white text-sm font-medium hover:bg-primary-900 transition-colors"
            >
              Далее
              <ChevronRight className="w-4 h-4" />
            </button>
          ) : (
            <button
              type="submit"
              disabled={isSubmitting}
              className="flex-1 flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl bg-success-600 text-white text-sm font-medium hover:bg-success-700 transition-colors disabled:opacity-60"
            >
              {isSubmitting ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Отправка…
                </>
              ) : (
                <>
                  <Check className="w-4 h-4" />
                  Подтвердить заявку
                </>
              )}
            </button>
          )}
        </div>
      </form>
    </div>
  );
}
