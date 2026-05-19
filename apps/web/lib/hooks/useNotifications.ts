import { useQuery } from '@tanstack/react-query';
import { notificationsApi } from '@/lib/api/notifications';
import { useAuthStore } from '@corp-portal/ui-core';

export function useNotifications(unreadOnly?: boolean) {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);

  return useQuery({
    queryKey: ['notifications', 'list', unreadOnly],
    queryFn: () =>
      notificationsApi.list({
        limit: 50,
        unreadOnly,
      }),
    enabled: isAuthenticated,
    staleTime: 30 * 1000,
  });
}

export function useUnreadNotificationsCount() {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);

  return useQuery({
    queryKey: ['notifications', 'unread-count'],
    queryFn: notificationsApi.getUnreadCount,
    enabled: isAuthenticated,
    staleTime: 30 * 1000,
    refetchInterval: 30 * 1000,
    refetchOnWindowFocus: true,
  });
}

export function useNotificationsBadge(): { unreadCount: number } {
  const { data } = useUnreadNotificationsCount();
  return { unreadCount: data ?? 0 };
}
