'use client';

import { useMemo } from 'react';
import Link from 'next/link';
import { Bell, Calendar, CheckCheck } from 'lucide-react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { useNotifications, useUnreadNotificationsCount } from '@/lib/hooks/useNotifications';
import { notificationsApi } from '@/lib/api/notifications';
import type { NotificationView } from '@/lib/types/views';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { formatRelativeDate, formatRelativeDateGroup } from '@corp-portal/ui-core';
import clsx from 'clsx';

const Box = 'section' as const;

function typeStyle(type: string): string {
  if (type === 'approved') return 'bg-success-100 text-success-600';
  if (type === 'rejected') return 'bg-danger-100 text-danger-600';
  if (type === 'pending' || type === 'approval_required') return 'bg-accent-100 text-accent-600';
  return 'bg-gray-100 text-gray-500';
}

function NotificationItem({
  notification,
  onMarkRead,
}: {
  notification: NotificationView;
  onMarkRead: (id: string) => void;
}) {
  const Icon = notification.type.includes('vacation') || notification.type === 'approved' || notification.type === 'rejected'
    ? Calendar
    : Bell;
  const colorClass = typeStyle(notification.type);
  const vacationId =
    notification.payload && typeof notification.payload.vacation_request_id === 'string'
      ? notification.payload.vacation_request_id
      : null;

  const content = (
    <Box
      className={clsx(
        'flex items-start gap-3 px-5 py-4 transition-colors w-full text-left',
        !notification.isRead
          ? 'bg-accent-50/50 hover:bg-accent-50'
          : 'hover:bg-gray-50'
      )}
      onClick={() => {
        if (!notification.isRead) onMarkRead(notification.id);
      }}
      role={vacationId ? undefined : 'button'}
      tabIndex={vacationId ? undefined : 0}
    >
      <Box className={clsx('w-9 h-9 rounded-full flex items-center justify-center flex-shrink-0', colorClass)}>
        <Icon className="w-4 h-4" />
      </Box>
      <Box className="flex-1 min-w-0">
        <Box className="flex items-start justify-between gap-2">
          <p
            className={clsx(
              'text-sm',
              !notification.isRead ? 'font-semibold text-gray-900' : 'font-medium text-gray-700'
            )}
          >
            {notification.title}
          </p>
          {!notification.isRead && (
            <span className="w-2 h-2 rounded-full bg-accent-500 flex-shrink-0 mt-1.5" />
          )}
        </Box>
        <p className="text-xs text-gray-500 mt-0.5 line-clamp-2">{notification.body}</p>
        <p className="text-[10px] text-gray-400 mt-1">{formatRelativeDate(notification.createdAt)}</p>
      </Box>
    </Box>
  );

  if (vacationId) {
    return (
      <Link href={`/vacations/detail?id=${vacationId}`} className="block">
        {content}
      </Link>
    );
  }

  return content;
}

export default function NotificationsPage() {
  const queryClient = useQueryClient();
  const { data, isLoading, isError } = useNotifications();
  const { data: unreadFromApi } = useUnreadNotificationsCount();

  const markReadMutation = useMutation({
    mutationFn: (id: string) => notificationsApi.markRead(id),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['notifications'] });
    },
  });

  const markAllReadMutation = useMutation({
    mutationFn: () => notificationsApi.markAllRead(),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['notifications'] });
    },
  });

  const allItems = useMemo(() => data?.items ?? [], [data?.items]);
  const unreadCount = unreadFromApi ?? allItems.filter((n) => !n.isRead).length;

  const grouped = useMemo(() => {
    const groups: Record<string, NotificationView[]> = {};
    for (const n of allItems) {
      const label = formatRelativeDateGroup(n.createdAt);
      if (!groups[label]) groups[label] = [];
      groups[label].push(n);
    }
    return groups;
  }, [allItems]);

  return (
    <Box className="space-y-5">
      <Box className="flex items-center justify-between">
        <Box>
          <h1 className="text-2xl font-bold text-gray-900">Уведомления</h1>
          {unreadCount > 0 && (
            <p className="text-sm text-gray-500 mt-0.5">{unreadCount} непрочитанных</p>
          )}
        </Box>
        {unreadCount > 0 && (
          <button
            type="button"
            onClick={() => markAllReadMutation.mutate()}
            disabled={markAllReadMutation.isPending}
            className="flex items-center gap-2 px-3 py-2 rounded-xl text-xs font-medium text-gray-600 hover:bg-gray-100 transition-colors disabled:opacity-50"
          >
            <CheckCheck className="w-4 h-4" />
            Прочитать все
          </button>
        )}
      </Box>

      {isLoading ? (
        <Box className="flex justify-center py-12">
          <LoadingSpinner size="lg" />
        </Box>
      ) : isError ? (
        <Box className="text-center py-12">
          <p className="text-gray-500">Не удалось загрузить уведомления</p>
        </Box>
      ) : allItems.length === 0 ? (
        <Box className="text-center py-16">
          <Box className="w-14 h-14 rounded-full bg-gray-100 flex items-center justify-center mx-auto mb-4">
            <Bell className="w-7 h-7 text-gray-400" />
          </Box>
          <p className="text-gray-700 font-medium">Уведомлений нет</p>
          <p className="text-gray-400 text-sm mt-1">Здесь будут появляться важные события</p>
        </Box>
      ) : (
        <Box className="space-y-5">
          {Object.entries(grouped).map(([dateLabel, notifications]) => (
            <Box key={dateLabel}>
              <h2 className="text-xs font-semibold text-gray-400 uppercase tracking-wide px-1 mb-2">
                {dateLabel}
              </h2>
              <Box className="bg-white rounded-2xl shadow-card overflow-hidden divide-y divide-gray-50">
                {notifications.map((notif) => (
                  <NotificationItem
                    key={notif.id}
                    notification={notif}
                    onMarkRead={(id) => markReadMutation.mutate(id)}
                  />
                ))}
              </Box>
            </Box>
          ))}
        </Box>
      )}
    </Box>
  );
}
