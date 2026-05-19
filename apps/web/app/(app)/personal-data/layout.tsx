'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
  User,
  Globe,
  CreditCard,
  MapPin,
  GraduationCap,
  Users,
  Phone,
  Heart,
  FileText,
  Building2,
  ClipboardList,
  CheckCircle2,
  Circle,
  Mail,
} from 'lucide-react';
import { clsx } from 'clsx';
import { useFullProfile } from '@/lib/hooks/usePersonalData';

interface SectionNavItem {
  href: string;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
  sectionKey: string;
}

const NAV_ITEMS: SectionNavItem[] = [
  { href: '/personal-data/basic', label: 'Основные данные', icon: User, sectionKey: 'personalData' },
  { href: '/personal-data/citizenship', label: 'Гражданство', icon: Globe, sectionKey: 'citizenship' },
  { href: '/personal-data/documents', label: 'Удостоверение', icon: CreditCard, sectionKey: 'documents' },
  { href: '/personal-data/contacts', label: 'Контакты', icon: Mail, sectionKey: 'contacts' },
  { href: '/personal-data/addresses', label: 'Адреса', icon: MapPin, sectionKey: 'addresses' },
  { href: '/personal-data/education', label: 'Образование', icon: GraduationCap, sectionKey: 'education' },
  { href: '/personal-data/family', label: 'Семья', icon: Users, sectionKey: 'family' },
  { href: '/personal-data/emergency', label: 'Экстренный контакт', icon: Phone, sectionKey: 'emergencyContact' },
  { href: '/personal-data/social', label: 'Социальные сведения', icon: Heart, sectionKey: 'socialInfo' },
  { href: '/personal-data/medical', label: 'Медицинские справки', icon: FileText, sectionKey: 'medicalCerts' },
  { href: '/personal-data/bank', label: 'Банковские реквизиты', icon: Building2, sectionKey: 'bankAccounts' },
  { href: '/personal-data/change-requests', label: 'Мои заявки', icon: ClipboardList, sectionKey: 'changeRequests' },
];

type ProfileKey = keyof {
  personalData: unknown;
  citizenship: unknown;
  documents: unknown;
  contacts: unknown;
  addresses: unknown;
  education: unknown;
  family: unknown;
  emergencyContact: unknown;
  socialInfo: unknown;
  medicalCerts: unknown;
  bankAccounts: unknown;
};

function getSectionStatus(
  sectionKey: string,
  profile: Record<string, unknown> | undefined
): 'filled' | 'partial' | 'empty' {
  if (!profile) return 'empty';

  const value = profile[sectionKey as ProfileKey];

  if (value === null || value === undefined) return 'empty';
  if (Array.isArray(value)) {
    return value.length > 0 ? 'filled' : 'empty';
  }
  if (typeof value === 'object') return 'filled';
  return 'empty';
}

export default function PersonalDataLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const { data: profile } = useFullProfile();

  const profileRecord = profile as unknown as Record<string, unknown> | undefined;

  return (
    <div className="space-y-4 min-w-0 max-w-full overflow-hidden">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Личные данные</h1>
        <p className="text-sm text-gray-500 mt-0.5">
          Управление персональной информацией
        </p>
      </div>

      <div className="flex flex-col lg:flex-row gap-4 lg:gap-6 items-stretch lg:items-start">
        {/* Sidebar nav */}
        <aside className="hidden lg:block w-56 flex-shrink-0">
          <nav className="bg-white rounded-2xl shadow-card p-2 space-y-0.5">
            {NAV_ITEMS.map((item) => {
              const isActive =
                item.href === '/personal-data'
                  ? pathname === '/personal-data'
                  : pathname.startsWith(item.href);
              const status = getSectionStatus(item.sectionKey, profileRecord);

              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={clsx(
                    'flex items-center gap-2.5 px-3 py-2 rounded-xl text-sm font-medium transition-all group',
                    isActive
                      ? 'bg-primary-800 text-white'
                      : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'
                  )}
                >
                  <item.icon
                    className={clsx(
                      'w-4 h-4 flex-shrink-0',
                      isActive ? 'text-white' : 'text-gray-400 group-hover:text-gray-600'
                    )}
                  />
                  <span className="flex-1 truncate">{item.label}</span>
                  {item.sectionKey !== 'changeRequests' && (
                    status === 'filled' ? (
                      <CheckCircle2
                        className={clsx(
                          'w-3.5 h-3.5 flex-shrink-0',
                          isActive ? 'text-white/80' : 'text-success-500'
                        )}
                      />
                    ) : status === 'partial' ? (
                      <Circle
                        className={clsx(
                          'w-3.5 h-3.5 flex-shrink-0',
                          isActive ? 'text-white/60' : 'text-warning-400'
                        )}
                      />
                    ) : null
                  )}
                </Link>
              );
            })}
          </nav>
        </aside>

        {/* Mobile horizontal scroll nav */}
        <div className="lg:hidden w-full max-w-full overflow-x-auto scrollbar-none">
          <div className="flex gap-2 min-w-max pb-0.5">
            {NAV_ITEMS.map((item) => {
              const isActive =
                item.href === '/personal-data'
                  ? pathname === '/personal-data'
                  : pathname.startsWith(item.href);
              const status = getSectionStatus(item.sectionKey, profileRecord);
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={clsx(
                    'flex items-center gap-1.5 px-3.5 py-2 rounded-full text-xs font-medium whitespace-nowrap transition-all border',
                    isActive
                      ? 'bg-primary-800 text-white border-primary-800'
                      : status === 'filled'
                      ? 'bg-success-50 text-success-700 border-success-200'
                      : 'bg-white text-gray-600 border-gray-200 hover:bg-gray-50'
                  )}
                >
                  <item.icon className="w-3.5 h-3.5 flex-shrink-0" />
                  {item.label}
                </Link>
              );
            })}
          </div>
        </div>

        {/* Main content */}
        <div className="w-full flex-1 min-w-0 max-w-full overflow-hidden">{children}</div>
      </div>
    </div>
  );
}
