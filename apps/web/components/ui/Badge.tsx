import { clsx } from 'clsx';
import type { VacationRequestStatus, SickLeaveStatus, TimesheetStatus } from '@corp-portal/shared-types';

type BadgeStatus = VacationRequestStatus | SickLeaveStatus | TimesheetStatus | string;

const STATUS_STYLES: Record<string, string> = {
  // VacationRequestStatus
  draft: 'bg-gray-100 text-gray-600 border-gray-200',
  pending: 'bg-warning-100 text-warning-700 border-warning-200',
  approved: 'bg-success-100 text-success-700 border-success-200',
  approved_by_manager: 'bg-accent-100 text-accent-700 border-accent-200',
  approved_by_hr: 'bg-success-100 text-success-700 border-success-200',
  rejected: 'bg-danger-100 text-danger-700 border-danger-200',
  cancelled: 'bg-gray-100 text-gray-500 border-gray-200',
  // SickLeaveStatus
  open: 'bg-warning-100 text-warning-700 border-warning-200',
  closed: 'bg-gray-100 text-gray-600 border-gray-200',
  confirmed: 'bg-success-100 text-success-700 border-success-200',
  // TimesheetStatus
  work: 'bg-success-100 text-success-700 border-success-200',
  overtime: 'bg-accent-100 text-accent-700 border-accent-200',
  partial: 'bg-orange-100 text-orange-700 border-orange-200',
  absence: 'bg-danger-100 text-danger-700 border-danger-200',
  vacation: 'bg-blue-100 text-blue-700 border-blue-200',
  sick: 'bg-warning-100 text-warning-700 border-warning-200',
  present: 'bg-success-100 text-success-700 border-success-200',
  absent: 'bg-danger-100 text-danger-700 border-danger-200',
  holiday: 'bg-purple-100 text-purple-700 border-purple-200',
  weekend: 'bg-gray-100 text-gray-400 border-gray-100',
  on_vacation: 'bg-blue-100 text-blue-700 border-blue-200',
  sick_leave: 'bg-warning-100 text-warning-700 border-warning-200',
  business_trip: 'bg-indigo-100 text-indigo-700 border-indigo-200',
  remote: 'bg-accent-100 text-accent-700 border-accent-200',
  half_day: 'bg-orange-100 text-orange-700 border-orange-200',
};

const STATUS_LABELS: Record<string, string> = {
  work: 'На работе',
  overtime: 'Сверхурочно',
  partial: 'Неполный день',
  absence: 'Отсутствие',
  vacation: 'Отпуск',
  sick: 'Больничный',
  draft: 'Черновик',
  pending: 'На рассмотрении',
  approved: 'Утверждён',
  approved_by_manager: 'Согласован',
  approved_by_hr: 'Утверждён',
  rejected: 'Отклонён',
  cancelled: 'Отменён',
  open: 'Открыт',
  closed: 'Закрыт',
  confirmed: 'Подтверждён',
  present: 'На работе',
  absent: 'Отсутствие',
  holiday: 'Праздник',
  weekend: 'Выходной',
  on_vacation: 'Отпуск',
  sick_leave: 'Больничный',
  business_trip: 'Командировка',
  remote: 'Удалённо',
  half_day: 'Неполный день',
};

interface BadgeProps {
  status: BadgeStatus;
  label?: string;
  className?: string;
  dot?: boolean;
}

export function Badge({ status, label, className, dot = false }: BadgeProps) {
  const key = status as string;
  const styleClass = STATUS_STYLES[key] ?? 'bg-gray-100 text-gray-600 border-gray-200';
  const displayLabel = label ?? STATUS_LABELS[key] ?? key;

  return (
    <span
      className={clsx(
        'inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium border',
        styleClass,
        className
      )}
    >
      {dot && (
        <span
          className={clsx(
            'w-1.5 h-1.5 rounded-full flex-shrink-0',
            key === 'pending' || key === 'open' ? 'animate-pulse' : ''
          )}
          style={{ background: 'currentColor' }}
        />
      )}
      {displayLabel}
    </span>
  );
}
