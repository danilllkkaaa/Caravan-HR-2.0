'use client';

import { Globe } from 'lucide-react';
import { useFullProfile } from '@/lib/hooks/usePersonalData';
import { DataSourceBadge } from '@/components/personal-data/DataSourceBadge';
import { PageLoader } from '@/components/ui/LoadingSpinner';

const STATUS_LABELS: Record<string, string> = {
  rk_citizen: 'Гражданин РК',
  foreign_citizen: 'Иностранный гражданин',
  stateless: 'Лицо без гражданства',
};

export default function CitizenshipPage() {
  const { data: profile, isLoading } = useFullProfile();

  if (isLoading) return <PageLoader />;

  const citizenship = profile?.citizenship ?? [];

  return (
    <div className="space-y-4">
      <h2 className="text-base font-semibold text-gray-900">Гражданство</h2>

      {citizenship.length === 0 ? (
        <div className="bg-white rounded-2xl shadow-card p-8 text-center">
          <Globe className="w-8 h-8 text-gray-300 mx-auto mb-3" />
          <p className="text-sm font-medium text-gray-900 mb-1">Сведения о гражданстве отсутствуют</p>
          <p className="text-xs text-gray-400">
            Данные о гражданстве поступают из 1С:ЗУП автоматически
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          {citizenship.map((item) => (
            <div key={item.id} className="bg-white rounded-2xl shadow-card p-4">
              <div className="flex items-center justify-between gap-3">
                <div>
                  <div className="flex items-center gap-2 mb-1">
                    <p className="text-sm font-semibold text-gray-900">{item.citizenship}</p>
                    {item.isPrimary && (
                      <span className="px-2 py-0.5 rounded-full text-xs font-medium bg-accent-100 text-accent-700 border border-accent-200">
                        Основное
                      </span>
                    )}
                  </div>
                  <p className="text-xs text-gray-500">{STATUS_LABELS[item.status] ?? item.status}</p>
                  {item.iinInCountry && (
                    <p className="text-xs text-gray-500 mt-0.5">
                      ИИН в стране: <span className="text-gray-700">{item.iinInCountry}</span>
                    </p>
                  )}
                </div>
                <DataSourceBadge source={item.source} />
              </div>
            </div>
          ))}
        </div>
      )}

      <div className="bg-blue-50 border border-blue-200 rounded-xl px-4 py-3 text-xs text-blue-800">
        Данные о гражданстве синхронизируются из 1С:ЗУП. Для изменения обратитесь к кадровику.
      </div>
    </div>
  );
}
