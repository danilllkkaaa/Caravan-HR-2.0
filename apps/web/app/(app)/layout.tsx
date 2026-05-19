'use client';

import { useEffect, useState } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import Image from 'next/image';
import Link from 'next/link';
import {
  Home,
  Umbrella,
  Thermometer,
  Clock,
  Users,
  CheckSquare,
  Bell,
  User,
  LogOut,
  ChevronRight,
  UserCircle,
  MoreHorizontal,
  X,
} from 'lucide-react';
import { useAuth } from '@corp-portal/ui-core';
import { useNotificationsBadge } from '@/lib/hooks/useNotifications';
import { PwaInstallBanner } from '@/components/ui/PwaInstallBanner';
import clsx from 'clsx';

function isManagerRole(role: string | undefined) {
  return ['manager', 'hr', 'admin'].includes(role ?? '');
}

interface NavItem {
  href: string;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
  badge?: number;
}

function SidebarNavItem({ item, isActive }: { item: NavItem; isActive: boolean }) {
  return (
    <Link
      href={item.href}
      className={clsx(
        'flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all group',
        isActive
          ? 'bg-primary-800 text-white shadow-sm'
          : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'
      )}
    >
      <item.icon
        className={clsx(
          'w-5 h-5 flex-shrink-0',
          isActive ? 'text-white' : 'text-gray-400 group-hover:text-gray-600'
        )}
      />
      <span className="flex-1">{item.label}</span>
      {item.badge && item.badge > 0 ? (
        <span
          className={clsx(
            'inline-flex items-center justify-center w-5 h-5 rounded-full text-xs font-bold',
            isActive ? 'bg-white text-primary-800' : 'bg-danger-500 text-white'
          )}
        >
          {item.badge > 99 ? '99+' : item.badge}
        </span>
      ) : null}
    </Link>
  );
}

function getPageTitle(pathname: string): string {
  if (pathname === '/') return 'Главная';
  if (pathname.startsWith('/vacations')) return 'Отпуска';
  if (pathname.startsWith('/sick-leaves')) return 'Больничные';
  if (pathname.startsWith('/timesheet')) return 'Табель';
  if (pathname.startsWith('/employees')) return 'Сотрудники';
  if (pathname.startsWith('/approvals')) return 'Согласования';
  if (pathname.startsWith('/notifications')) return 'Уведомления';
  if (pathname.startsWith('/personal-data')) return 'Личные данные';
  if (pathname.startsWith('/profile')) return 'Профиль';
  if (pathname.startsWith('/resignation')) return 'Увольнение';
  return 'HR Портал';
}

export default function AppLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const { user, employee, isAuthenticated, isHydrated, isSessionRestoring, logout } = useAuth();
  const { unreadCount } = useNotificationsBadge();
  const [moreOpen, setMoreOpen] = useState(false);

  // Close drawer on navigation
  useEffect(() => {
    setMoreOpen(false);
  }, [pathname]);

  useEffect(() => {
    if (isHydrated && !isSessionRestoring && !isAuthenticated) {
      router.push('/login');
    }
  }, [isHydrated, isAuthenticated, isSessionRestoring, router]);

  if (!isHydrated || isSessionRestoring || !isAuthenticated) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="w-8 h-8 border-4 border-primary-800 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  const role =
    (employee as { role?: string } | null)?.role ??
    (user?.role as string | undefined);
  const isManager = isManagerRole(role);

  const allNavItems: NavItem[] = [
    { href: '/', label: 'Главная', icon: Home },
    { href: '/vacations', label: 'Отпуска', icon: Umbrella },
    { href: '/sick-leaves', label: 'Больничные', icon: Thermometer },
    { href: '/timesheet', label: 'Табель', icon: Clock },
    ...(isManager
      ? [
          { href: '/employees', label: 'Сотрудники', icon: Users },
          { href: '/approvals', label: 'Согласования', icon: CheckSquare },
        ]
      : []),
    { href: '/notifications', label: 'Уведомления', icon: Bell, badge: unreadCount },
    { href: '/personal-data', label: 'Личные данные', icon: UserCircle },
    { href: '/profile', label: 'Профиль', icon: User },
  ];

  // Fixed 4 items always visible in bottom bar
  const bottomNavItems: NavItem[] = [
    { href: '/', label: 'Главная', icon: Home },
    { href: '/vacations', label: 'Отпуска', icon: Umbrella },
    { href: '/sick-leaves', label: 'Больничный', icon: Thermometer },
    { href: '/notifications', label: 'Уведомления', icon: Bell, badge: unreadCount },
  ];

  // Everything else goes into the "More" drawer
  const moreDrawerItems: NavItem[] = [
    { href: '/timesheet', label: 'Табель', icon: Clock },
    { href: '/personal-data', label: 'Личные данные', icon: UserCircle },
    { href: '/profile', label: 'Профиль', icon: User },
    ...(isManager
      ? [
          { href: '/employees', label: 'Сотрудники', icon: Users },
          { href: '/approvals', label: 'Согласования', icon: CheckSquare },
        ]
      : []),
  ];

  const handleLogout = async () => {
    setMoreOpen(false);
    await logout();
    router.push('/login');
  };

  const isItemActive = (href: string) =>
    href === '/' ? pathname === '/' : pathname.startsWith(href);

  const isMoreActive = moreDrawerItems.some((item) => isItemActive(item.href));

  return (
    <div className="min-h-screen flex bg-gray-50">
      {/* ─────────────────── Desktop sidebar ─────────────────── */}
      <aside className="hidden md:flex flex-col w-64 bg-white border-r border-gray-200 fixed top-0 left-0 h-full z-30">
        {/* Logo */}
        <div className="flex items-center gap-3 px-4 py-5 border-b border-gray-100">
          <div className="w-8 h-8 rounded-lg bg-primary-800 flex items-center justify-center">
            <svg
              className="w-4 h-4 text-white"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth={2}
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M2.25 21h19.5m-18-18v18m10.5-18v18m6-13.5V21M6.75 6.75h.75m-.75 3h.75m-.75 3h.75m3-6h.75m-.75 3h.75m-.75 3h.75M6.75 21v-3.375c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125V21"
              />
            </svg>
          </div>
          <div>
            <p className="text-sm font-semibold text-gray-900">Корп. портал</p>
            <p className="text-xs text-gray-500">HR-система</p>
          </div>
        </div>

        {/* Nav */}
        <nav className="flex-1 overflow-y-auto px-3 py-4 space-y-1">
          {allNavItems.map((item) => (
            <SidebarNavItem
              key={item.href}
              item={item}
              isActive={isItemActive(item.href)}
            />
          ))}
        </nav>

        {/* User section */}
        <div className="px-3 py-4 border-t border-gray-100">
          <div className="flex items-center gap-3 px-3 py-2 mb-2">
            <div className="w-8 h-8 rounded-full bg-primary-100 flex items-center justify-center flex-shrink-0">
              {employee?.avatarUrl ? (
                <Image
                  src={employee.avatarUrl}
                  alt={employee.fullName}
                  width={32}
                  height={32}
                  className="w-8 h-8 rounded-full object-cover"
                />
              ) : (
                <span className="text-xs font-bold text-primary-700">
                  {employee?.firstName?.[0]}
                  {employee?.lastName?.[0]}
                </span>
              )}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-gray-900 truncate">
                {employee?.fullName ?? user?.email}
              </p>
              <p className="text-xs text-gray-500 truncate">
                {(employee as { position?: { title?: string } } | null)?.position?.title ?? role}
              </p>
            </div>
            <ChevronRight className="w-4 h-4 text-gray-400" />
          </div>
          <button
            onClick={handleLogout}
            className="w-full flex items-center gap-2 px-3 py-2 rounded-xl text-sm text-gray-600 hover:bg-danger-50 hover:text-danger-600 transition-colors"
          >
            <LogOut className="w-4 h-4" />
            Выйти
          </button>
        </div>
      </aside>

      {/* ─────────────────── Mobile header ─────────────────── */}
      <header className="md:hidden fixed top-0 left-0 right-0 bg-white border-b border-gray-100 z-30">
        {/* Safe area spacer for notch / Dynamic Island */}
        <div className="safe-top" />
        <div className="flex items-center justify-between px-4 h-14">
          {/* Logo + page title */}
          <div className="flex items-center gap-2.5 min-w-0">
            <div className="w-7 h-7 flex-shrink-0 rounded-lg bg-primary-800 flex items-center justify-center">
              <svg
                className="w-3.5 h-3.5 text-white"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                strokeWidth={2}
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M2.25 21h19.5m-18-18v18m10.5-18v18m6-13.5V21M6.75 6.75h.75m-.75 3h.75m-.75 3h.75m3-6h.75m-.75 3h.75m-.75 3h.75M6.75 21v-3.375c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125V21"
                />
              </svg>
            </div>
            <span className="text-sm font-semibold text-gray-900 truncate">
              {getPageTitle(pathname)}
            </span>
          </div>

          {/* Notification bell */}
          <Link
            href="/notifications"
            className="relative p-2 -mr-1 rounded-xl hover:bg-gray-100 transition-colors"
          >
            <Bell className="w-5 h-5 text-gray-600" />
            {unreadCount > 0 && (
              <span className="absolute top-1.5 right-1.5 w-4 h-4 bg-danger-500 text-white text-[10px] font-bold rounded-full flex items-center justify-center leading-none">
                {unreadCount > 9 ? '9+' : unreadCount}
              </span>
            )}
          </Link>
        </div>
      </header>

      {/* ─────────────────── "More" backdrop ─────────────────── */}
      <div
        className={clsx(
          'md:hidden fixed inset-0 z-40 bg-black/40 backdrop-blur-sm transition-opacity duration-300',
          moreOpen ? 'opacity-100 pointer-events-auto' : 'opacity-0 pointer-events-none'
        )}
        onClick={() => setMoreOpen(false)}
      />

      {/* ─────────────────── "More" slide-up drawer ─────────────────── */}
      <div
        className={clsx(
          'md:hidden fixed bottom-0 left-0 right-0 bg-white rounded-t-3xl z-50 transition-transform duration-300 ease-out shadow-modal',
          moreOpen ? 'translate-y-0' : 'translate-y-full'
        )}
      >
        {/* Drag handle */}
        <div className="flex justify-center pt-3 pb-1">
          <div className="w-10 h-1 rounded-full bg-gray-200" />
        </div>

        {/* Header */}
        <div className="flex items-center justify-between px-5 py-2">
          <span className="text-sm font-semibold text-gray-900">Меню</span>
          <button
            onClick={() => setMoreOpen(false)}
            className="p-1.5 rounded-xl hover:bg-gray-100 transition-colors"
          >
            <X className="w-4 h-4 text-gray-500" />
          </button>
        </div>

        {/* Nav items */}
        <nav className="px-4 py-1 space-y-0.5">
          {moreDrawerItems.map((item) => {
            const active = isItemActive(item.href);
            return (
              <Link
                key={item.href}
                href={item.href}
                className={clsx(
                  'flex items-center gap-3 px-4 py-3 rounded-2xl text-sm font-medium transition-all',
                  active
                    ? 'bg-primary-800 text-white'
                    : 'text-gray-700 hover:bg-gray-50'
                )}
              >
                <item.icon
                  className={clsx('w-5 h-5 flex-shrink-0', active ? 'text-white' : 'text-gray-400')}
                />
                <span className="flex-1">{item.label}</span>
                {item.badge && item.badge > 0 ? (
                  <span
                    className={clsx(
                      'inline-flex items-center justify-center w-5 h-5 rounded-full text-xs font-bold',
                      active ? 'bg-white text-primary-800' : 'bg-danger-500 text-white'
                    )}
                  >
                    {item.badge > 99 ? '99+' : item.badge}
                  </span>
                ) : null}
              </Link>
            );
          })}
        </nav>

        {/* Divider */}
        <div className="mx-5 my-2 border-t border-gray-100" />

        {/* User info + logout */}
        <div className="px-4 pb-4">
          <div className="flex items-center gap-3 px-4 py-2.5 mb-0.5">
            <div className="w-9 h-9 rounded-full bg-primary-100 flex items-center justify-center flex-shrink-0">
              {employee?.avatarUrl ? (
                <Image
                  src={employee.avatarUrl}
                  alt={employee.fullName}
                  width={36}
                  height={36}
                  className="w-9 h-9 rounded-full object-cover"
                />
              ) : (
                <span className="text-sm font-bold text-primary-700">
                  {employee?.firstName?.[0]}
                  {employee?.lastName?.[0]}
                </span>
              )}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-semibold text-gray-900 truncate">
                {employee?.fullName ?? user?.email}
              </p>
              <p className="text-xs text-gray-500 truncate">{role}</p>
            </div>
          </div>
          <button
            onClick={handleLogout}
            className="w-full flex items-center gap-3 px-4 py-3 rounded-2xl text-sm text-danger-600 font-medium hover:bg-danger-50 transition-colors"
          >
            <LogOut className="w-5 h-5" />
            Выйти из системы
          </button>
        </div>

        {/* Safe area spacer at bottom of drawer */}
        <div className="safe-bottom" />
      </div>

      {/* ─────────────────── Mobile bottom nav ─────────────────── */}
      <nav className="md:hidden fixed bottom-0 left-0 right-0 bg-white border-t border-gray-100 z-30">
        <div className="flex items-center justify-around px-1 py-1">
          {bottomNavItems.map((item) => {
            const active = isItemActive(item.href);
            return (
              <Link
                key={item.href}
                href={item.href}
                className={clsx(
                  'flex flex-col items-center gap-0.5 flex-1 py-2 rounded-xl min-w-0 relative transition-colors',
                  active ? 'text-primary-800' : 'text-gray-400'
                )}
              >
                <item.icon className="w-5 h-5" />
                {item.badge && item.badge > 0 ? (
                  <span className="absolute top-1.5 right-[calc(50%-18px)] w-4 h-4 bg-danger-500 text-white text-[10px] font-bold rounded-full flex items-center justify-center leading-none">
                    {item.badge > 9 ? '9+' : item.badge}
                  </span>
                ) : null}
                <span className="text-[10px] font-medium leading-tight truncate max-w-[56px] text-center">
                  {item.label}
                </span>
              </Link>
            );
          })}

          {/* "More" button */}
          <button
            onClick={() => setMoreOpen(true)}
            className={clsx(
              'flex flex-col items-center gap-0.5 flex-1 py-2 rounded-xl transition-colors',
              moreOpen || isMoreActive ? 'text-primary-800' : 'text-gray-400'
            )}
          >
            <MoreHorizontal className="w-5 h-5" />
            <span className="text-[10px] font-medium leading-tight">Ещё</span>
          </button>
        </div>
        {/* Safe area spacer for home indicator */}
        <div className="safe-bottom" />
      </nav>

      {/* ─────────────────── PWA install banner ─────────────────── */}
      <PwaInstallBanner />

      {/* ─────────────────── Main content ─────────────────── */}
      <main className="flex-1 min-w-0 max-w-full overflow-x-hidden md:ml-64 min-h-screen">
        {/* pt accounts for: mobile header (h-14 = 56px) + safe-top area */}
        {/* pb accounts for: bottom nav (~56px) + safe-bottom area */}
        <div className="pt-header pb-nav md:pt-0 md:pb-0">
          <div className="max-w-5xl mx-auto px-4 md:px-6 py-6">{children}</div>
        </div>
      </main>
    </div>
  );
}
