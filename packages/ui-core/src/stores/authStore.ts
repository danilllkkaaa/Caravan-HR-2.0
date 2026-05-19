import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import type { User, Employee } from '@corp-portal/shared-types';

export interface AuthState {
  user: User | null;
  employee: Employee | null;
  accessToken: string | null;
  isAuthenticated: boolean;
  isHydrated: boolean;
}

export interface AuthActions {
  login: (user: User, employee: Employee, accessToken: string) => void;
  logout: () => void;
  setAccessToken: (token: string) => void;
  setUser: (user: User, employee: Employee) => void;
  setHydrated: () => void;
}

export type AuthStore = AuthState & AuthActions;

export const useAuthStore = create<AuthStore>()(
  persist(
    (set) => ({
      // State
      user: null,
      employee: null,
      accessToken: null,
      isAuthenticated: false,
      isHydrated: false,

      // Actions
      login: (user, employee, accessToken) =>
        set({
          user,
          employee,
          accessToken,
          isAuthenticated: true,
        }),

      logout: () =>
        set({
          user: null,
          employee: null,
          accessToken: null,
          isAuthenticated: false,
        }),

      setAccessToken: (token) =>
        set({
          accessToken: token,
          isAuthenticated: true,
        }),

      setUser: (user, employee) =>
        set({
          user,
          employee,
        }),

      setHydrated: () => set({ isHydrated: true }),
    }),
    {
      name: 'auth-storage',
      storage: createJSONStorage(() =>
        typeof window !== 'undefined' ? localStorage : {
          getItem: () => null,
          setItem: () => undefined,
          removeItem: () => undefined,
        }
      ),
      // Only persist these fields — accessToken is short-lived
      // and stored in memory; refresh token is handled via httpOnly cookie
      partialize: (state) => ({
        user: state.user,
        employee: state.employee,
        // We do NOT persist the access token to localStorage for security.
        // On page reload, the app will call /auth/refresh using the cookie.
      }),
      onRehydrateStorage: () => (state) => {
        state?.setHydrated();
      },
    }
  )
);
