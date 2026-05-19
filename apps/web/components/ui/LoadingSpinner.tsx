import { clsx } from 'clsx';

type SpinnerSize = 'xs' | 'sm' | 'md' | 'lg' | 'xl';

const SIZE_CLASSES: Record<SpinnerSize, string> = {
  xs: 'w-3 h-3 border-[2px]',
  sm: 'w-4 h-4 border-[2px]',
  md: 'w-6 h-6 border-2',
  lg: 'w-8 h-8 border-[3px]',
  xl: 'w-12 h-12 border-4',
};

interface LoadingSpinnerProps {
  size?: SpinnerSize;
  className?: string;
  color?: 'primary' | 'white' | 'gray';
}

const COLOR_CLASSES: Record<string, string> = {
  primary: 'border-primary-200 border-t-primary-800',
  white: 'border-white/30 border-t-white',
  gray: 'border-gray-200 border-t-gray-600',
};

export function LoadingSpinner({
  size = 'md',
  className,
  color = 'primary',
}: LoadingSpinnerProps) {
  return (
    <div
      role="status"
      aria-label="Загрузка…"
      className={clsx(
        'rounded-full animate-spin',
        SIZE_CLASSES[size],
        COLOR_CLASSES[color],
        className
      )}
    />
  );
}

export function PageLoader({ label = 'Загрузка…' }: { label?: string }) {
  return (
    <div className="flex flex-col items-center justify-center gap-3 py-20">
      <LoadingSpinner size="lg" />
      <p className="text-sm text-gray-400">{label}</p>
    </div>
  );
}
