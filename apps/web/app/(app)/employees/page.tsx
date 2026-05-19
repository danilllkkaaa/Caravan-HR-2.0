'use client';

import { useEffect, useState } from 'react';
import { Search, Users, Phone, Mail, Building2, ChevronRight, X } from 'lucide-react';
import Image from 'next/image';
import Link from 'next/link';
import { useEmployees, useDepartments } from '@/lib/hooks/useEmployees';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import type { Employee, Department } from '@corp-portal/shared-types';
import clsx from 'clsx';

function useDebounce<T>(value: T, delay: number): T {
  const [debouncedValue, setDebouncedValue] = useState<T>(value);

  useEffect(() => {
    const timeout = setTimeout(() => setDebouncedValue(value), delay);
    return () => clearTimeout(timeout);
  }, [delay, value]);

  return debouncedValue;
}

function EmployeeCard({ employee }: { employee: Employee }) {
  return (
    <Link
      href={`/employees/${employee.id}`}
      className="flex items-center gap-4 bg-white rounded-2xl shadow-card hover:shadow-card-hover transition-shadow p-4 group"
    >
      {/* Avatar */}
      <div className="w-12 h-12 rounded-full bg-primary-100 flex items-center justify-center flex-shrink-0">
        {employee.avatarUrl ? (
          <Image
            src={employee.avatarUrl}
            alt={employee.fullName}
            width={48}
            height={48}
            className="w-12 h-12 rounded-full object-cover"
          />
        ) : (
          <span className="text-base font-bold text-primary-700">
            {employee.firstName[0]}{employee.lastName[0]}
          </span>
        )}
      </div>

      {/* Info */}
      <div className="flex-1 min-w-0">
        <p className="text-sm font-semibold text-gray-900 truncate">{employee.fullName}</p>
        <p className="text-xs text-gray-500 truncate mt-0.5">{employee.position.title}</p>
        <div className="flex items-center gap-3 mt-1.5">
          <span className="flex items-center gap-1 text-xs text-gray-400">
            <Building2 className="w-3 h-3" />
            <span className="truncate max-w-[120px]">{employee.department.name}</span>
          </span>
          {employee.phone && (
            <span className="flex items-center gap-1 text-xs text-gray-400">
              <Phone className="w-3 h-3" />
              <span>{employee.phone}</span>
            </span>
          )}
        </div>
      </div>

      <ChevronRight className="w-4 h-4 text-gray-300 group-hover:text-gray-500 transition-colors flex-shrink-0" />
    </Link>
  );
}

function DepartmentFilter({
  departments,
  selected,
  onChange,
}: {
  departments: Department[];
  selected: string | undefined;
  onChange: (id: string | undefined) => void;
}) {
  return (
    <div className="flex flex-wrap gap-2">
      <button
        onClick={() => onChange(undefined)}
        className={clsx(
          'px-3 py-1.5 rounded-lg text-xs font-medium transition-colors',
          selected === undefined
            ? 'bg-primary-800 text-white'
            : 'bg-white text-gray-600 border border-gray-200 hover:bg-gray-50'
        )}
      >
        Все отделы
      </button>
      {departments.map((dept) => (
        <button
          key={dept.id}
          onClick={() => onChange(String(dept.id))}
          className={clsx(
            'px-3 py-1.5 rounded-lg text-xs font-medium transition-colors',
            selected === String(dept.id)
              ? 'bg-primary-800 text-white'
              : 'bg-white text-gray-600 border border-gray-200 hover:bg-gray-50'
          )}
        >
          {dept.name}
        </button>
      ))}
    </div>
  );
}

export default function EmployeesPage() {
  const [search, setSearch] = useState('');
  const [selectedDept, setSelectedDept] = useState<string | undefined>(undefined);
  const [page, setPage] = useState(1);

  const debouncedSearch = useDebounce(search, 300);

  const { data, isLoading, isError, isFetching } = useEmployees({
    search: debouncedSearch || undefined,
    departmentId: selectedDept,
    page,
    pageSize: 20,
  });

  const { data: departments } = useDepartments();

  const employees = data?.items ?? [];
  const totalPages = data ? Math.ceil(data.total / 20) : 1;

  const handleSearch = (value: string) => {
    setSearch(value);
    setPage(1);
  };

  const handleDeptChange = (id: string | undefined) => {
    setSelectedDept(id);
    setPage(1);
  };

  return (
    <div className="space-y-5">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Сотрудники</h1>
        <p className="text-gray-500 text-sm mt-0.5">
          {data ? `${data.total} сотрудников` : 'Список сотрудников'}
        </p>
      </div>

      {/* Search */}
      <div className="relative">
        <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
        <input
          type="search"
          value={search}
          onChange={(e) => handleSearch(e.target.value)}
          placeholder="Поиск по имени, должности…"
          className="w-full pl-10 pr-10 py-2.5 rounded-xl border border-gray-200 bg-white text-sm
            outline-none focus:ring-2 focus:ring-accent-500 focus:border-accent-500 transition-colors"
        />
        {search && (
          <button
            onClick={() => handleSearch('')}
            className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
          >
            <X className="w-4 h-4" />
          </button>
        )}
      </div>

      {/* Department filter */}
      {departments && departments.length > 0 && (
        <DepartmentFilter
          departments={departments}
          selected={selectedDept}
          onChange={handleDeptChange}
        />
      )}

      {/* Content */}
      {isLoading ? (
        <div className="flex justify-center py-16">
          <LoadingSpinner size="lg" />
        </div>
      ) : isError ? (
        <div className="text-center py-16">
          <p className="text-gray-500">Не удалось загрузить список сотрудников</p>
        </div>
      ) : employees.length === 0 ? (
        <div className="text-center py-16">
          <div className="w-14 h-14 rounded-full bg-gray-100 flex items-center justify-center mx-auto mb-4">
            <Users className="w-7 h-7 text-gray-400" />
          </div>
          <p className="text-gray-700 font-medium">Сотрудники не найдены</p>
          {debouncedSearch && (
            <p className="text-gray-400 text-sm mt-1">
              По запросу «{debouncedSearch}» ничего не найдено
            </p>
          )}
        </div>
      ) : (
        <div className="space-y-3">
          {/* Loading overlay for subsequent fetches */}
          <div className={clsx('transition-opacity', isFetching ? 'opacity-60' : 'opacity-100')}>
            {employees.map((emp) => (
              <EmployeeCard key={emp.id} employee={emp} />
            ))}
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-center gap-2 pt-2">
              <button
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page === 1 || isFetching}
                className="px-4 py-2 rounded-xl border border-gray-200 text-sm font-medium text-gray-700
                  hover:bg-gray-50 transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
              >
                Назад
              </button>
              <span className="text-sm text-gray-500 px-2">
                {page} / {totalPages}
              </span>
              <button
                onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                disabled={page === totalPages || isFetching}
                className="px-4 py-2 rounded-xl border border-gray-200 text-sm font-medium text-gray-700
                  hover:bg-gray-50 transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
              >
                Вперёд
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
