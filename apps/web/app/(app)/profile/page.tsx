'use client';

import { useRouter } from 'next/navigation';
import Image from 'next/image';
import {
  User,
  Building2,
  Phone,
  Mail,
  MapPin,
  Calendar,
  Lock,
  Smartphone,
  LogOut,
  ChevronRight,
  Shield,
  UserCircle,
} from 'lucide-react';
import { useAuth } from '@corp-portal/ui-core';
import { formatDateRu } from '@corp-portal/ui-core';
import { useMyEmployee } from '@/lib/hooks/useEmployees';
import clsx from 'clsx';

const Box = 'section' as const;

const ROLE_LABELS: Record<string, string> = {
  employee: 'Сотрудник',
  manager: 'Руководитель',
  hr: 'HR-специалист',
  admin: 'Администратор',
};

function InfoRow({
  icon: Icon,
  label,
  value,
}: {
  icon: React.ComponentType<{ className?: string }>;
  label: string;
  value?: string | null;
}) {
  if (!value) return null;
  return (
    <Box className="flex items-start gap-3 px-5 py-3.5">
      <Icon className="w-4 h-4 text-gray-400 mt-0.5 flex-shrink-0" />
      <Box>
        <p className="text-xs text-gray-400">{label}</p>
        <p className="text-sm font-medium text-gray-900 mt-0.5">{value}</p>
      </Box>
    </Box>
  );
}

function ActionRow({
  icon: Icon,
  label,
  description,
  onClick,
  danger,
}: {
  icon: React.ComponentType<{ className?: string }>;
  label: string;
  description?: string;
  onClick: () => void;
  danger?: boolean;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={clsx(
        'w-full flex items-center gap-3 px-5 py-3.5 transition-colors text-left',
        danger ? 'hover:bg-danger-50' : 'hover:bg-gray-50'
      )}
    >
      <Box
        className={clsx(
          'w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0',
          danger ? 'bg-danger-100' : 'bg-gray-100'
        )}
      >
        <Icon className={clsx('w-4 h-4', danger ? 'text-danger-600' : 'text-gray-500')} />
      </Box>
      <Box className="flex-1">
        <p className={clsx('text-sm font-medium', danger ? 'text-danger-700' : 'text-gray-900')}>
          {label}
        </p>
        {description && <p className="text-xs text-gray-400 mt-0.5">{description}</p>}
      </Box>
      <ChevronRight className="w-4 h-4 text-gray-300" />
    </button>
  );
}

export default function ProfilePage() {
  const router = useRouter();
  const { user, employee, logout } = useAuth();
  const { data: freshEmployee } = useMyEmployee(Boolean(user));

  const handleLogout = async () => {
    await logout();
    router.push('/login');
  };

  if (!user || !employee) {
    return (
      <Box className="flex justify-center py-12">
        <Box className="w-8 h-8 border-4 border-primary-800 border-t-transparent rounded-full animate-spin" />
      </Box>
    );
  }

  const profileEmployee = freshEmployee ?? employee;
  const roleKey =
    (profileEmployee as { role?: string }).role ?? (user.role as string | undefined) ?? 'employee';
  const positionTitle = (profileEmployee as { position?: { title?: string } }).position?.title;
  const departmentName = (profileEmployee as { department?: { name?: string } }).department?.name;
  const managerName = (profileEmployee as { manager?: { fullName?: string } }).manager?.fullName;
  const workLocationName = (profileEmployee as { workLocation?: { name?: string } }).workLocation?.name;
  const hireDate = (profileEmployee as { hireDate?: string }).hireDate;
  const employeeNumber =
    (profileEmployee as { employeeNumber?: string }).employeeNumber ??
    (profileEmployee as { personnelNumber?: string }).personnelNumber;
  const phone = (profileEmployee as { phone?: string }).phone;

  return (
    <Box className="space-y-5 max-w-lg mx-auto">
      <Box>
        <h1 className="text-2xl font-bold text-gray-900">Профиль</h1>
      </Box>

      <Box className="bg-white rounded-2xl shadow-card p-6">
        <Box className="flex items-center gap-4">
          <Box className="w-16 h-16 rounded-2xl bg-primary-100 flex items-center justify-center flex-shrink-0">
            {profileEmployee.avatarUrl ? (
              <Image
                src={profileEmployee.avatarUrl}
                alt={profileEmployee.fullName}
                width={64}
                height={64}
                className="w-16 h-16 rounded-2xl object-cover"
              />
            ) : (
              <span className="text-xl font-bold text-primary-700">
                {profileEmployee.firstName[0]}
                {profileEmployee.lastName[0]}
              </span>
            )}
          </Box>
          <Box>
            <h2 className="text-lg font-bold text-gray-900">{profileEmployee.fullName}</h2>
            {positionTitle && <p className="text-sm text-gray-500">{positionTitle}</p>}
            <Box className="flex items-center gap-1.5 mt-1.5">
              <Shield className="w-3.5 h-3.5 text-accent-500" />
              <span className="text-xs font-medium text-accent-700 bg-accent-50 px-2 py-0.5 rounded-full">
                {ROLE_LABELS[roleKey] ?? roleKey}
              </span>
            </Box>
          </Box>
        </Box>
      </Box>

      <Box className="bg-white rounded-2xl shadow-card overflow-hidden">
        <Box className="px-5 py-3 border-b border-gray-50">
          <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wide">
            Рабочая информация
          </h3>
        </Box>
        <Box className="divide-y divide-gray-50">
          <InfoRow icon={Building2} label="Подразделение" value={departmentName} />
          <InfoRow icon={User} label="Должность" value={positionTitle} />
          <InfoRow icon={User} label="Руководитель" value={managerName} />
          <InfoRow icon={MapPin} label="Место работы" value={workLocationName} />
          <InfoRow
            icon={Calendar}
            label="Дата приёма"
            value={hireDate ? formatDateRu(hireDate) : null}
          />
          <InfoRow icon={User} label="Табельный номер" value={employeeNumber} />
        </Box>
      </Box>

      <Box className="bg-white rounded-2xl shadow-card overflow-hidden">
        <Box className="px-5 py-3 border-b border-gray-50">
          <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wide">Контакты</h3>
        </Box>
        <Box className="divide-y divide-gray-50">
          <InfoRow icon={Mail} label="Email" value={user.email} />
          <InfoRow icon={Phone} label="Телефон" value={phone} />
        </Box>
      </Box>

      <Box className="bg-white rounded-2xl shadow-card overflow-hidden">
        <Box className="px-5 py-3 border-b border-gray-50">
          <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wide">Личное</h3>
        </Box>
        <Box className="divide-y divide-gray-50">
          <ActionRow
            icon={UserCircle}
            label="Личные данные"
            description="Документы, адреса, образование, семья и банковские реквизиты"
            onClick={() => router.push('/personal-data')}
          />
        </Box>
      </Box>

      <Box className="bg-white rounded-2xl shadow-card overflow-hidden">
        <Box className="px-5 py-3 border-b border-gray-50">
          <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wide">Действия</h3>
        </Box>
        <Box className="divide-y divide-gray-50">
          <ActionRow
            icon={Lock}
            label="Изменить пароль"
            description="Смена текущего пароля аккаунта"
            onClick={() => router.push('/profile/change-password')}
          />
          <ActionRow
            icon={Smartphone}
            label="Мои устройства"
            description="Активные сессии и устройства"
            onClick={() => router.push('/profile/sessions')}
          />
          <ActionRow
            icon={LogOut}
            label="Выйти из системы"
            onClick={() => void handleLogout()}
            danger
          />
        </Box>
      </Box>

      <p className="text-center text-xs text-gray-300 pb-4">
        Корпоративный портал · v1.0.0
      </p>
    </Box>
  );
}
