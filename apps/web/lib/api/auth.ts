import type {
  LoginRequest,
  LoginResponse,
  User,
  Employee,
  UserSession,
  ChangePasswordRequest,
} from '@corp-portal/shared-types';
import { apiDelete, apiGet, apiPost } from './client';

interface BackendTokenResponse {
  access_token: string;
  token_type: string;
  refresh_expires_at: string;
  refresh_token: string;
}

interface BackendMeResponse {
  id: string;
  email: string;
  is_active: boolean;
  employee: {
    id: string;
    personnel_number: string;
    first_name: string;
    last_name: string;
    middle_name: string;
    role: string;
    department_id: string;
    position_id: string;
    avatar_url: string | null;
  };
}

interface BackendSessionResponse {
  id: string;
  device_info: Record<string, unknown>;
  created_at: string;
  expires_at: string;
}

function mapMe(data: BackendMeResponse): { user: User; employee: Employee } {
  const user = {
    id: data.id,
    email: data.email,
    role: data.employee.role,
    isActive: data.is_active,
  } as unknown as User;

  const employee = {
    id: data.employee.id,
    userId: data.id,
    firstName: data.employee.first_name,
    lastName: data.employee.last_name,
    middleName: data.employee.middle_name,
    fullName: `${data.employee.last_name} ${data.employee.first_name}`.trim(),
    avatarUrl: data.employee.avatar_url,
    employeeNumber: data.employee.personnel_number,
    role: data.employee.role,
  } as unknown as Employee;

  return { user, employee };
}

export const authApi = {
  /**
   * Authenticate with email + password.
   * Server sets httpOnly refresh token cookie automatically.
   */
  login: async (data: LoginRequest): Promise<LoginResponse> => {
    const token = await apiPost<BackendTokenResponse>('/auth/login', {
      email: data.email.trim().toLowerCase(),
      password: data.password,
    });
    const me = await apiGet<BackendMeResponse>('/auth/me', {
      headers: { Authorization: `Bearer ${token.access_token}` },
    });
    const mapped = mapMe(me);

    return {
      accessToken: token.access_token,
      tokenType: token.token_type,
      expiresIn: 15 * 60,
      ...mapped,
    };
  },

  /**
   * Logout: revokes current refresh token (via cookie).
   */
  logout: () => apiPost<void>('/auth/logout'),

  /**
   * Refresh access token using httpOnly cookie.
   */
  refresh: () =>
    apiPost<BackendTokenResponse>('/auth/refresh').then((data) => ({
      accessToken: data.access_token,
      expiresIn: 15 * 60,
    })),

  /**
   * Get current authenticated user info.
   */
  getMe: () => apiGet<BackendMeResponse>('/auth/me').then(mapMe),

  /**
   * Get active sessions / devices for current user.
   */
  getSessions: () =>
    apiGet<BackendSessionResponse[]>('/auth/sessions').then((items) =>
      items.map((item) => ({
        id: item.id,
        deviceInfo: item.device_info,
        ipAddress:
          typeof item.device_info.ip === 'string' ? item.device_info.ip : null,
        createdAt: item.created_at,
        lastUsedAt: item.created_at,
        expiresAt: item.expires_at,
        isCurrent: false,
      })) as unknown as UserSession[]
    ),

  /**
   * Revoke a specific session.
   */
  revokeSession: (sessionId: number | string) =>
    apiDelete<void>(`/auth/sessions/${sessionId}`),

  /**
   * Revoke all other sessions (keep current).
   */
  revokeAllSessions: () => apiPost<void>('/auth/logout-all'),

  /**
   * Change password.
   */
  changePassword: (data: ChangePasswordRequest) =>
    apiPost<void>('/auth/change-password', {
      current_password: data.currentPassword,
      new_password: data.newPassword,
    }),
};
