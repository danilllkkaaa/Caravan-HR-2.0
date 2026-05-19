import { useCallback, useEffect, useRef, useState } from 'react';
import { useAuthStore } from '../stores/authStore';
import { resolveApiBaseUrl } from '../utils/apiBase';

const REFRESH_SAFETY_WINDOW_MS = 60 * 1000;
const MIN_REFRESH_DELAY_MS = 30 * 1000;
const FALLBACK_REFRESH_DELAY_MS = 12 * 60 * 1000;

interface RefreshResponse {
  access_token: string;
  token_type: string;
  refresh_expires_at: string;
  refresh_token: string;
}

function getAccessTokenRefreshDelay(token: string): number {
  try {
    const payload = token.split('.')[1];
    if (!payload) return FALLBACK_REFRESH_DELAY_MS;

    const normalized = payload.replace(/-/g, '+').replace(/_/g, '/');
    const decoded = JSON.parse(window.atob(normalized)) as { exp?: number };
    if (!decoded.exp) return FALLBACK_REFRESH_DELAY_MS;

    const delay = decoded.exp * 1000 - Date.now() - REFRESH_SAFETY_WINDOW_MS;
    return Math.max(MIN_REFRESH_DELAY_MS, delay);
  } catch {
    return FALLBACK_REFRESH_DELAY_MS;
  }
}

export function useAuth() {
  const {
    user,
    employee,
    accessToken,
    isAuthenticated,
    isHydrated,
    login,
    logout,
    setAccessToken,
    setUser,
  } = useAuthStore();

  const refreshTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const [isSessionRestoring, setIsSessionRestoring] = useState(true);

  const refresh = useCallback(async (): Promise<string | null> => {
    try {
      const response = await fetch(`${resolveApiBaseUrl()}/api/v1/auth/refresh`, {
        method: 'POST',
        credentials: 'include', // sends httpOnly refresh token cookie
        headers: { 'Content-Type': 'application/json' },
      });

      if (!response.ok) {
        const currentToken = useAuthStore.getState().accessToken;
        if ((response.status === 401 || response.status === 403) && !currentToken) {
          logout();
        }
        return null;
      }

      const data = (await response.json()) as RefreshResponse;
      setAccessToken(data.access_token);
      return data.access_token;
    } catch {
      return null;
    }
  }, [logout, setAccessToken]);

  // Schedule next refresh
  const scheduleRefresh = useCallback((token: string) => {
    if (refreshTimerRef.current) {
      clearTimeout(refreshTimerRef.current);
    }
    refreshTimerRef.current = setTimeout(() => {
      void refresh().then((token) => {
        if (token) scheduleRefresh(token);
      });
    }, getAccessTokenRefreshDelay(token));
  }, [refresh]);

  // On mount: if hydrated and we have a user but no access token, try refresh
  useEffect(() => {
    if (!isHydrated) return;

    let cancelled = false;

    async function restoreSession() {
      if (user && !accessToken) {
        const token = await refresh();
        if (token) scheduleRefresh(token);
      } else if (isAuthenticated && accessToken) {
        scheduleRefresh(accessToken);
      }

      if (!cancelled) {
        setIsSessionRestoring(false);
      }
    }

    void restoreSession();

    return () => {
      cancelled = true;
      if (refreshTimerRef.current) {
        clearTimeout(refreshTimerRef.current);
      }
    };
  }, [accessToken, isAuthenticated, isHydrated, refresh, scheduleRefresh, user]);

  useEffect(() => {
    if (user && !accessToken) {
      setIsSessionRestoring(true);
    }
  }, [accessToken, user]);

  const signOut = useCallback(async () => {
    try {
      if (accessToken) {
        await fetch(`${resolveApiBaseUrl()}/api/v1/auth/logout`, {
          method: 'POST',
          credentials: 'include',
          headers: {
            Authorization: `Bearer ${accessToken}`,
            'Content-Type': 'application/json',
          },
        });
      }
    } finally {
      logout();
      if (refreshTimerRef.current) {
        clearTimeout(refreshTimerRef.current);
      }
    }
  }, [accessToken, logout]);

  return {
    user,
    employee,
    accessToken,
    isAuthenticated,
    isHydrated,
    isSessionRestoring,
    login,
    logout: signOut,
    setUser,
    refresh,
  };
}
