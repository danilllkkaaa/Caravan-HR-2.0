import type {
  Employee,
  Department,
  Position,
  PaginatedResponse,
} from '@corp-portal/shared-types';
import { apiGet, apiPatch } from './client';

interface ListEmployeesParams {
  page?: number;
  pageSize?: number;
  departmentId?: string;
  search?: string;
  isActive?: boolean;
}

interface BackendEmployee {
  id: string;
  user_id: string;
  personnel_number: string;
  first_name: string;
  last_name: string;
  middle_name: string;
  phone: string;
  department_id: string;
  position_id: string;
  manager_id: string | null;
  role: string;
  hire_date: string;
  avatar_url: string | null;
  created_at: string;
  updated_at: string;
}

interface BackendDepartment {
  id: string;
  external_id_1c: string;
  name: string;
  parent_id: string | null;
  head_id: string | null;
}

interface BackendPosition {
  id: string;
  external_id_1c: string;
  name: string;
  department_id: string | null;
}

interface BackendPaginatedEmployees {
  items: BackendEmployee[];
  total: number;
  offset: number;
  limit: number;
}

function mapDepartment(data: BackendDepartment): Department {
  return {
    id: data.id,
    name: data.name,
    code: data.external_id_1c,
    parentId: data.parent_id,
    managerId: data.head_id,
  } as unknown as Department;
}

function mapPosition(data: BackendPosition): Position {
  return {
    id: data.id,
    title: data.name,
    code: data.external_id_1c,
    departmentId: data.department_id,
  } as unknown as Position;
}

function mapEmployee(data: BackendEmployee): Employee {
  const department = {
    id: data.department_id,
    name: '',
    code: '',
  } as unknown as Department;
  const position = {
    id: data.position_id,
    title: '',
    code: '',
  } as unknown as Position;

  return {
    id: data.id,
    userId: data.user_id,
    firstName: data.first_name,
    lastName: data.last_name,
    middleName: data.middle_name || null,
    fullName: `${data.last_name} ${data.first_name}`.trim(),
    phone: data.phone || null,
    avatarUrl: data.avatar_url,
    hireDate: data.hire_date,
    dismissDate: null,
    departmentId: data.department_id,
    department,
    positionId: data.position_id,
    position,
    managerId: data.manager_id,
    manager: null,
    workLocationId: null,
    workLocation: null,
    employeeNumber: data.personnel_number,
    isActive: true,
    createdAt: data.created_at,
    updatedAt: data.updated_at,
    role: data.role,
  } as unknown as Employee;
}

function mapListParams(params?: ListEmployeesParams) {
  const page = params?.page ?? 1;
  const pageSize = params?.pageSize ?? 20;
  return {
    search: params?.search,
    department_id: params?.departmentId,
    offset: (page - 1) * pageSize,
    limit: pageSize,
  };
}

export const employeesApi = {
  /**
   * List employees (manager/HR/admin).
   */
  list: async (params?: ListEmployeesParams): Promise<PaginatedResponse<Employee>> => {
    const response = await apiGet<BackendPaginatedEmployees>('/employees', {
      params: mapListParams(params),
    });
    const pageSize = response.limit;
    const page = Math.floor(response.offset / pageSize) + 1;
    const totalPages = Math.max(1, Math.ceil(response.total / pageSize));
    return {
      items: response.items.map(mapEmployee),
      total: response.total,
      page,
      pageSize,
      totalPages,
      hasNext: page < totalPages,
      hasPrev: page > 1,
    };
  },

  /**
   * Get a single employee by ID.
   */
  getById: (id: string) =>
    apiGet<BackendEmployee>(`/employees/${id}`).then(mapEmployee),

  /**
   * Get the current employee's own profile.
   */
  getMe: () =>
    apiGet<BackendEmployee>('/employees/me').then(mapEmployee),

  /**
   * Update the current employee's own profile (limited fields).
   */
  updateMe: (data: Partial<Pick<Employee, 'phone'>>) =>
    apiPatch<BackendEmployee>('/employees/me', data).then(mapEmployee),

  /**
   * Get all departments.
   */
  getDepartments: () =>
    apiGet<BackendDepartment[]>('/departments').then((items) => items.map(mapDepartment)),

  /**
   * Get positions, optionally filtered by department.
   */
  getPositions: (departmentId?: string) =>
    apiGet<BackendPosition[]>('/positions', {
      params: { department_id: departmentId },
    }).then((items) => items.map(mapPosition)),

  /**
   * Get direct reports for the current manager.
   */
  getDirectReports: () =>
    apiGet<BackendEmployee[]>('/employees/direct-reports').then((items) =>
      items.map(mapEmployee)
    ),
};
