import { clsx } from 'clsx';
import type { DataSource } from '@corp-portal/shared-types';

interface DataSourceBadgeProps {
  source: DataSource;
  className?: string;
}

const SOURCE_CONFIG: Record<
  DataSource,
  { label: string; classes: string }
> = {
  '1c': {
    label: '\u{1F504} Из 1С:ЗУП',
    classes: 'bg-blue-50 text-blue-700 border-blue-200',
  },
  user: {
    label: '✏️ Заполнено вами',
    classes: 'bg-gray-100 text-gray-600 border-gray-200',
  },
  hr_approved: {
    label: '✅ Подтверждено HR',
    classes: 'bg-success-50 text-success-700 border-success-200',
  },
};

export function DataSourceBadge({ source, className }: DataSourceBadgeProps) {
  const config = SOURCE_CONFIG[source];
  return (
    <span
      className={clsx(
        'inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium border',
        config.classes,
        className
      )}
    >
      {config.label}
    </span>
  );
}
