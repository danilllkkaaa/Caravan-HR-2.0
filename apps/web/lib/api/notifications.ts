import { apiGet, apiPost } from './client';
import { mapNotification, type BackendNotification } from './mappers';
import type { NotificationView, OffsetList } from '@/lib/types/views';

interface ListNotificationsParams {
  offset?: number;
  limit?: number;
  unreadOnly?: boolean;
}

export const notificationsApi = {
  list: async (params?: ListNotificationsParams): Promise<OffsetList<NotificationView>> => {
    const res = await apiGet<OffsetList<BackendNotification>>('/notifications', {
      params: {
        offset: params?.offset ?? 0,
        limit: params?.limit ?? 20,
        unread_only: params?.unreadOnly ?? false,
      },
    });
    return { ...res, items: res.items.map(mapNotification) };
  },

  getUnreadCount: () =>
    apiGet<{ count: number }>('/notifications/unread-count').then((r) => r.count),

  markRead: async (id: string) => {
    const raw = await apiPost<BackendNotification>(`/notifications/${id}/read`);
    return mapNotification(raw);
  },

  markAllRead: () => apiPost<void>('/notifications/read-all'),
};
