import axios, {
  type AxiosError,
  type AxiosInstance,
  type AxiosRequestConfig,
  type InternalAxiosRequestConfig,
} from 'axios';
import type { ApiError } from '@corp-portal/shared-types';
import { resolveApiBaseUrl, useAuthStore } from '@corp-portal/ui-core';

const API_BASE_URL = resolveApiBaseUrl();

let isRefreshing = false;
let refreshSubscribers: Array<(token: string) => void> = [];

function onRefreshed(token: string) {
  refreshSubscribers.forEach((cb) => cb(token));
  refreshSubscribers = [];
}

function addRefreshSubscriber(cb: (token: string) => void) {
  refreshSubscribers.push(cb);
}

export class ApiClientError extends Error {
  constructor(
    public readonly code: string,
    message: string,
    public readonly details?: unknown,
    public readonly status?: number
  ) {
    super(message);
    this.name = 'ApiClientError';
  }
}

function normalizeError(error: AxiosError<ApiError>): never {
  const status = error.response?.status;
  const apiError = error.response?.data?.error;

  if (apiError) {
    throw new ApiClientError(
      apiError.code,
      apiError.message,
      apiError.details,
      status
    );
  }

  if (status === 401) throw new ApiClientError('UNAUTHORIZED', 'Необходима авторизация', undefined, 401);
  if (status === 403) throw new ApiClientError('FORBIDDEN', 'Доступ запрещен', undefined, 403);
  if (status === 404) throw new ApiClientError('NOT_FOUND', 'Ресурс не найден', undefined, 404);
  if (status === 422) throw new ApiClientError('VALIDATION_ERROR', 'Ошибка валидации', error.response?.data, 422);
  if (status === 429) throw new ApiClientError('RATE_LIMITED', 'Слишком много запросов. Попробуйте позже.', undefined, 429);
  if (status && status >= 500) throw new ApiClientError('SERVER_ERROR', 'Ошибка сервера. Попробуйте позже.', undefined, status);
  if (error.code === 'ECONNABORTED') throw new ApiClientError('TIMEOUT', 'Время ожидания истекло', undefined);
  if (!error.response) throw new ApiClientError('NETWORK_ERROR', 'Нет соединения с сервером', undefined);

  throw new ApiClientError('UNKNOWN', error.message ?? 'Неизвестная ошибка', undefined, status);
}

function createApiClient(): AxiosInstance {
  const client = axios.create({
    baseURL: `${API_BASE_URL}/api/v1`,
    timeout: 30_000,
    withCredentials: true,
    headers: {
      'Content-Type': 'application/json',
      Accept: 'application/json',
    },
  });

  client.interceptors.request.use(
    (config: InternalAxiosRequestConfig) => {
      const token = useAuthStore.getState().accessToken;
      if (token && config.headers) {
        config.headers.Authorization = `Bearer ${token}`;
      }
      return config;
    },
    (error) => Promise.reject(error)
  );

  client.interceptors.response.use(
    (response) => response,
    async (error: AxiosError<ApiError>) => {
      const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean };

      if (
        error.response?.status === 401 &&
        !originalRequest._retry &&
        !originalRequest.url?.includes('/auth/refresh') &&
        !originalRequest.url?.includes('/auth/login')
      ) {
        if (isRefreshing) {
          return new Promise<string>((resolve) => {
            addRefreshSubscriber(resolve);
          }).then((token) => {
            if (originalRequest.headers) {
              originalRequest.headers.Authorization = `Bearer ${token}`;
            }
            return client(originalRequest);
          });
        }

        originalRequest._retry = true;
        isRefreshing = true;

        try {
          const response = await axios.post<{ access_token: string }>(
            `${API_BASE_URL}/api/v1/auth/refresh`,
            {},
            { withCredentials: true }
          );

          const newToken = response.data.access_token;
          useAuthStore.getState().setAccessToken(newToken);
          onRefreshed(newToken);

          if (originalRequest.headers) {
            originalRequest.headers.Authorization = `Bearer ${newToken}`;
          }
          return client(originalRequest);
        } catch (refreshError) {
          if (
            axios.isAxiosError(refreshError) &&
            (refreshError.response?.status === 401 || refreshError.response?.status === 403)
          ) {
            useAuthStore.getState().logout();
            if (typeof window !== 'undefined') {
              window.location.href = '/login';
            }
          }
          return Promise.reject(error);
        } finally {
          isRefreshing = false;
        }
      }

      return normalizeError(error);
    }
  );

  return client;
}

export const apiClient = createApiClient();

export async function apiGet<T>(
  url: string,
  config?: AxiosRequestConfig
): Promise<T> {
  const response = await apiClient.get<T>(url, config);
  return response.data;
}

export async function apiPost<T>(
  url: string,
  data?: unknown,
  config?: AxiosRequestConfig
): Promise<T> {
  const response = await apiClient.post<T>(url, data, config);
  return response.data;
}

export async function apiPut<T>(
  url: string,
  data?: unknown,
  config?: AxiosRequestConfig
): Promise<T> {
  const response = await apiClient.put<T>(url, data, config);
  return response.data;
}

export async function apiPatch<T>(
  url: string,
  data?: unknown,
  config?: AxiosRequestConfig
): Promise<T> {
  const response = await apiClient.patch<T>(url, data, config);
  return response.data;
}

export async function apiDelete<T = void>(
  url: string,
  config?: AxiosRequestConfig
): Promise<T> {
  const response = await apiClient.delete<T>(url, config);
  return response.data;
}
