'use client';

import Link from 'next/link';
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
  ChevronRight,
  Info,
  ClipboardList,
  Mail,
} from 'lucide-react';
import { useFullProfile, useChangeRequests } from '@/lib/hooks/usePersonalData';
import { PageLoader } from '@/components/ui/LoadingSpinner';
import { Badge } from '@/components/ui/Badge';
import { ChangeRequestStatus } from '@corp-portal/shared-types';

const SECTION_CARDS = [
  {
    href: '/personal-data/basic',
    label: 'Основные данные',
    description: 'ФИО, пол, национальность, место рождения',
    icon: User,
    sectionKey: 'personalData',
  },
  {
    href: '/personal-data/citizenship',
    label: 'Гражданство',
    description: 'Гражданство и ИИН',
    icon: Globe,
    sectionKey: 'citizenship',
  },
  {
    href: '/personal-data/documents',
    label: 'Удостоверение личности',
    description: 'Паспорт, удостоверение, вид на жительство',
    icon: CreditCard,
    sectionKey: 'documents',
  },
  {
    href: '/personal-data/contacts',
    label: 'Контакты',
    description: 'Email, мобильный, домашний и дополнительный телефон',
    icon: Mail,
    sectionKey: 'contacts',
  },
  {
    href: '/personal-data/addresses',
    label: 'Адреса',
    description: 'Регистрация и фактическое проживание',
    icon: MapPin,
    sectionKey: 'addresses',
  },
  {
    href: '/personal-data/education',
    label: 'Образование',
    description: 'Учебные заведения, специальности',
    icon: GraduationCap,
    sectionKey: 'education',
  },
  {
    href: '/personal-data/family',
    label: 'Семья',
    description: 'Супруг(а), дети',
    icon: Users,
    sectionKey: 'family',
  },
  {
    href: '/personal-data/emergency',
    label: 'Экстренный контакт',
    description: 'Контакт для связи в экстренных случаях',
    icon: Phone,
    sectionKey: 'emergencyContact',
  },
  {
    href: '/personal-data/social',
    label: 'Социальные сведения',
    description: 'Инвалидность, ветеранский статус, пенсия',
    icon: Heart,
    sectionKey: 'socialInfo',
  },
  {
    href: '/personal-data/medical',
    label: 'Медицинские справки',
    description: 'Наркологическая, психиатрическая, форма 075',
    icon: FileText,
    sectionKey: 'medicalCerts',
  },
  {
    href: '/personal-data/bank',
    label: 'Банковские реквизиты',
    description: 'Расчётные счета для выплат',
    icon: Building2,
    sectionKey: 'bankAccounts',
  },
];

const STATUS_LABELS: Record<ChangeRequestStatus, string> = {
  [ChangeRequestStatus.Sent]: 'Отправлена',
  [ChangeRequestStatus.UnderReview]: 'На рассмотрении',
  [ChangeRequestStatus.Approved]: 'Одобрена',
  [ChangeRequestStatus.Rejected]: 'Отклонена',
};

function getSectionFilled(sectionKey: string, profile: Record<string, unknown> | undefined): boolean {
  if (!profile) return false;
  const value = profile[sectionKey];
  if (value === null || value === undefined) return false;
  if (Array.isArray(value)) return value.length > 0;
  return true;
}

export default function PersonalDataPage() {
  const { data: profile, isLoading } = useFullProfile();
  const { data: changeRequests } = useChangeRequests();

  if (isLoading) return <PageLoader />;

  const profileRecord = profile as unknown as Record<string, unknown> | undefined;
  const filledCount = SECTION_CARDS.filter((s) =>
    getSectionFilled(s.sectionKey, profileRecord)
  ).length;
  const totalCount = SECTION_CARDS.length;
  const fillPercent = Math.round((filledCount / totalCount) * 100);

  const recentRequests = changeRequests?.slice(0, 3) ?? [];

  return (
    <div className="space-y-5 min-w-0 max-w-full">
      {/* Progress card */}
      <div className="bg-white rounded-2xl shadow-card p-5 min-w-0 overflow-hidden">
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-sm font-semibold text-gray-900">Заполненность профиля</h2>
          <span className="text-2xl font-bold text-primary-800">{fillPercent}%</span>
        </div>
        <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
          <div
            className="h-full bg-primary-800 rounded-full transition-all"
            style={{ width: `${fillPercent}%` }}
          />
        </div>
        <p className="text-xs text-gray-500 mt-2">
          {filledCount} из {totalCount} разделов заполнено
        </p>
      </div>

      {/* Info banner */}
      <div className="flex gap-3 bg-blue-50 border border-blue-200 rounded-xl px-4 py-3 min-w-0 overflow-hidden">
        <Info className="w-4 h-4 text-blue-600 flex-shrink-0 mt-0.5" />
        <p className="text-sm text-blue-800 min-w-0 break-words">
          Данные из 1С:ЗУП обновляются автоматически. Для изменения таких данных подайте заявку кадровику.
        </p>
      </div>

      {/* Section cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 min-w-0">
        {SECTION_CARDS.map((card) => {
          const isFilled = getSectionFilled(card.sectionKey, profileRecord);
          return (
            <Link
              key={card.href}
              href={card.href}
              className="flex items-center gap-3 bg-white rounded-2xl shadow-card px-4 py-4 hover:shadow-md transition-shadow group min-w-0 max-w-full overflow-hidden"
            >
              <div
                className={`w-9 h-9 rounded-xl flex items-center justify-center flex-shrink-0 ${
                  isFilled ? 'bg-success-50' : 'bg-gray-100'
                }`}
              >
                <card.icon
                  className={`w-5 h-5 ${isFilled ? 'text-success-600' : 'text-gray-400'}`}
                />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-semibold text-gray-900">{card.label}</p>
                <p className="text-xs text-gray-400 truncate">{card.description}</p>
              </div>
              <ChevronRight className="w-4 h-4 text-gray-300 group-hover:text-gray-500 transition-colors" />
            </Link>
          );
        })}
      </div>

      {/* Change requests block */}
      {recentRequests.length > 0 && (
        <div className="bg-white rounded-2xl shadow-card overflow-hidden">
          <div className="flex items-center justify-between px-5 py-3 border-b border-gray-50">
            <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wide">
              Последние заявки на изменение
            </h3>
            <Link
              href="/personal-data/change-requests"
              className="text-xs text-accent-600 hover:text-accent-800 font-medium"
            >
              Все заявки
            </Link>
          </div>
          <div className="divide-y divide-gray-50">
            {recentRequests.map((req) => (
              <div key={req.id} className="flex items-center gap-3 px-5 py-3.5">
                <ClipboardList className="w-4 h-4 text-gray-400 flex-shrink-0" />
                <div className="flex-1 min-w-0">
                  <p className="text-sm text-gray-900 truncate">{req.fieldName}</p>
                  <p className="text-xs text-gray-400">
                    {new Date(req.createdAt).toLocaleDateString('ru-RU')}
                  </p>
                </div>
                <Badge status={req.status} label={STATUS_LABELS[req.status]} />
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}


