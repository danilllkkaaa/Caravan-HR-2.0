'use client';

import { format } from 'date-fns';
import { ru } from 'date-fns/locale';
import { CalendarPlus, Clock, Bell, ArrowRight, TrendingUp, CheckSquare } from 'lucide-react';
import Link from 'next/link';
import { useAuthStore } from '@corp-portal/ui-core';
import { useDashboard } from '@/lib/hooks/useDashboard';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { formatRelativeDate } from '@corp-portal/ui-core';
import type { NotificationView } from '@/lib/types/views';
import clsx from 'clsx';

const Box = 'section' as const;

function VacationBalanceCard({
  total,
  used,
  remaining,
}: {
  total: number;
  used: number;
  remaining: number;
}) {
  const pct = total > 0 ? Math.min((used / total) * 100, 100) : 0;

  return (
    <Box className="bg-white rounded-2xl p-5 shadow-card">
      <Box className="flex items-start justify-between mb-3">
        <Box>
          <p className="text-xs font-medium text-gray-500 uppercase tracking-wide">
            Ежегодный отпуск
          </p>
          <p className="text-2xl font-bold text-gray-900 mt-0.5">
            {remaining} <span className="text-base font-normal text-gray-500">дн.</span>
          </p>
        </Box>
        <TrendingUp className="w-5 h-5 text-accent-500 mt-1" />
      </Box>
      <Box className="h-2 bg-gray-100 rounded-full overflow-hidden mb-3">
        <Box className="h-full bg-accent-500 transition-all" style={{ width: `${pct}%` }} />
      </Box>
      <Box className="flex items-center justify-between text-xs text-gray-500">
        <span>Использовано: {used} дн.</span>
        <span>Всего: {total} дн.</span>
      </Box>
    </Box>
  );
}

function QuickActionButton({
  href,
  icon: Icon,
  label,
  description,
}: {
  href: string;
  icon: React.ComponentType<{ className?: string }>;
  label: string;
  description: string;
}) {
  return (
    <Link
      href={href}
      className="flex items-center gap-3 p-4 bg-white rounded-2xl shadow-card hover:shadow-card-hover transition-shadow group"
    >
      <Box className="w-10 h-10 rounded-xl bg-primary-50 flex items-center justify-center group-hover:bg-primary-100 transition-colors flex-shrink-0">
        <Icon className="w-5 h-5 text-primary-700" />
      </Box>
      <Box className="flex-1 min-w-0">
        <p className="text-sm font-semibold text-gray-900">{label}</p>
        <p className="text-xs text-gray-500 truncate">{description}</p>
      </Box>
      <ArrowRight className="w-4 h-4 text-gray-400 group-hover:text-gray-600 flex-shrink-0" />
    </Link>
  );
}

function notificationIcon(type: string) {
  if (type === 'approved' || type === 'rejected') return CalendarPlus;
  return Bell;
}

function NotificationRow({ notif }: { notif: NotificationView }) {
  const Icon = notificationIcon(notif.type);
  const vacationId =
    notif.payload && typeof notif.payload.vacation_request_id === 'string'
      ? notif.payload.vacation_request_id
      : null;

  const inner = (
    <>
      <Box className="w-8 h-8 rounded-full bg-gray-100 flex items-center justify-center flex-shrink-0 mt-0.5">
        <Icon className="w-4 h-4 text-gray-500" />
      </Box>
      <Box className="flex-1 min-w-0">
        <p
          className={clsx(
            'text-sm',
            !notif.isRead ? 'font-semibold text-gray-900' : 'font-medium text-gray-700'
          )}
        >
          {notif.title}
        </p>
        <p className="text-xs text-gray-500 mt-0.5 line-clamp-1">{notif.body}</p>
      </Box>
      <span className="text-xs text-gray-400 flex-shrink-0 ml-2">
        {formatRelativeDate(notif.createdAt)}
      </span>
    </>
  );

  if (vacationId) {
    return (
      <Link
        href={`/vacations/detail?id=${vacationId}`}
        className={clsx(
          'flex items-start gap-3 px-5 py-4 hover:bg-gray-50 transition-colors',
          !notif.isRead && 'bg-accent-50/40'
        )}
      >
        {inner}
      </Link>
    );
  }

  return (
    <Box
      className={clsx(
        'flex items-start gap-3 px-5 py-4',
        !notif.isRead && 'bg-accent-50/40'
      )}
    >
      {inner}
    </Box>
  );
}

function NotificationsBlock({ items }: { items: NotificationView[] }) {
  return (
    <Box>
      <Box className="flex items-center justify-between mb-3">
        <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide">
          Последние уведомления
        </h2>
        <Link
          href="/notifications"
          className="text-xs text-accent-600 hover:underline font-medium"
        >
          Все уведомления
        </Link>
      </Box>
      <Box className="bg-white rounded-2xl shadow-card divide-y divide-gray-50">
        {items.slice(0, 3).map((notif) => (
          <NotificationRow key={notif.id} notif={notif} />
        ))}
      </Box>
    </Box>
  );
}

function isManagerRole(role: string | undefined) {
  return ['manager', 'hr', 'admin'].includes(role ?? '');
}

export default function DashboardPage() {
  const employee = useAuthStore((s) => s.employee);
  const { data, isLoading, isError } = useDashboard();

  const today = format(new Date(), 'EEEE, d MMMM yyyy', { locale: ru });
  const todayCapitalized = today.charAt(0).toUpperCase() + today.slice(1);
  const isManager = isManagerRole((employee as { role?: string } | null)?.role);

  if (isLoading) {
    return (
      <Box className="flex items-center justify-center min-h-[60vh]">
        <LoadingSpinner size="lg" />
      </Box>
    );
  }

  if (isError || !data) {
    return (
      <Box className="flex flex-col items-center justify-center min-h-[60vh] text-center">
        <p className="text-gray-500 mb-4">Не удалось загрузить данные</p>
        <button
          type="button"
          onClick={() => window.location.reload()}
          className="text-sm text-accent-600 hover:underline"
        >
          Попробовать снова
        </button>
      </Box>
    );
  }

  const balance = data.vacationBalance;
  const unread = data.recentNotifications.filter((n) => !n.isRead).length;

  return (
    <Box className="space-y-6">
      <Box>
        <h1 className="text-2xl font-bold text-gray-900">
          Добрый день, {data.employee.firstName}!
        </h1>
        <p className="text-gray-500 mt-0.5">{todayCapitalized}</p>
      </Box>

      <VacationBalanceCard
        total={balance.totalDays}
        used={balance.usedDays}
        remaining={balance.availableDays}
      />

      <Box>
        <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-3">
          Быстрые действия
        </h2>
        <Box className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <QuickActionButton
            href="/vacations/new"
            icon={CalendarPlus}
            label="Новый отпуск"
            description="Подать заявку на отпуск"
          />
          {isManager && (
            <QuickActionButton
              href="/approvals"
              icon={CheckSquare}
              label="Согласования"
              description="Заявки на одобрение"
            />
          )}
          <QuickActionButton
            href="/timesheet"
            icon={Clock}
            label="Мой табель"
            description="Учёт рабочего времени"
          />
          <QuickActionButton
            href="/notifications"
            icon={Bell}
            label="Уведомления"
            description={unread > 0 ? `${unread} непрочитанных` : 'Все уведомления'}
          />
        </Box>
      </Box>

      {data.recentNotifications.length > 0 && (
        <NotificationsBlock items={data.recentNotifications} />
      )}
    </Box>
  );
}
