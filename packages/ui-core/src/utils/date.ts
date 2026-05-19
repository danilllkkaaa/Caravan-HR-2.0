import {
  format,
  formatRelative,
  formatDistanceToNow,
  differenceInCalendarDays,
  isWeekend,
  addDays,
  isSameDay,
  parseISO,
  isValid,
} from 'date-fns';
import { ru } from 'date-fns/locale';

/**
 * Format a date relative to now in Russian.
 * Example: "5 минут назад", "вчера в 14:30", "12 мар."
 */
export function formatRelativeDate(date: Date | string): string {
  const d = typeof date === 'string' ? parseISO(date) : date;
  if (!isValid(d)) return '—';

  return formatDistanceToNow(d, { addSuffix: true, locale: ru });
}

/**
 * Format a date in a human-readable Russian format.
 * @param date - ISO string or Date
 * @param fmt - date-fns format string (default: 'd MMMM yyyy')
 */
export function formatDateRu(
  date: Date | string,
  fmt: string = 'd MMMM yyyy'
): string {
  const d = typeof date === 'string' ? parseISO(date) : date;
  if (!isValid(d)) return '—';

  return format(d, fmt, { locale: ru });
}

/**
 * Format a date range in Russian.
 * Example: "12 марта — 25 марта 2024"
 */
export function formatDateRangeRu(
  startDate: Date | string,
  endDate: Date | string
): string {
  const start = typeof startDate === 'string' ? parseISO(startDate) : startDate;
  const end = typeof endDate === 'string' ? parseISO(endDate) : endDate;

  if (!isValid(start) || !isValid(end)) return '—';

  const startYear = format(start, 'yyyy');
  const endYear = format(end, 'yyyy');

  if (startYear === endYear) {
    return `${format(start, 'd MMMM', { locale: ru })} — ${format(end, 'd MMMM yyyy', { locale: ru })}`;
  }

  return `${format(start, 'd MMMM yyyy', { locale: ru })} — ${format(end, 'd MMMM yyyy', { locale: ru })}`;
}

/**
 * Format a time in HH:mm format.
 */
export function formatTime(date: Date | string): string {
  const d = typeof date === 'string' ? parseISO(date) : date;
  if (!isValid(d)) return '—';

  return format(d, 'HH:mm');
}

/**
 * Calculate the number of working days between two dates (inclusive),
 * excluding weekends. Does not account for public holidays.
 */
export function calculateWorkdays(
  startDate: Date | string,
  endDate: Date | string
): number {
  const start = typeof startDate === 'string' ? parseISO(startDate) : startDate;
  const end = typeof endDate === 'string' ? parseISO(endDate) : endDate;

  if (!isValid(start) || !isValid(end)) return 0;
  if (end < start) return 0;

  let count = 0;
  let current = start;

  while (current <= end) {
    if (!isWeekend(current)) {
      count++;
    }
    current = addDays(current, 1);
  }

  return count;
}

/**
 * Calculate the total number of calendar days between two dates (inclusive).
 */
export function calculateCalendarDays(
  startDate: Date | string,
  endDate: Date | string
): number {
  const start = typeof startDate === 'string' ? parseISO(startDate) : startDate;
  const end = typeof endDate === 'string' ? parseISO(endDate) : endDate;

  if (!isValid(start) || !isValid(end)) return 0;

  return differenceInCalendarDays(end, start) + 1;
}

/**
 * Format a duration in hours and minutes as a Russian string.
 * Example: "8 ч 30 мин", "1 ч", "45 мин"
 */
export function formatDuration(totalMinutes: number): string {
  if (totalMinutes <= 0) return '0 мин';

  const hours = Math.floor(totalMinutes / 60);
  const minutes = totalMinutes % 60;

  if (hours === 0) return `${minutes} мин`;
  if (minutes === 0) return `${hours} ч`;

  return `${hours} ч ${minutes} мин`;
}

/**
 * Format hours as a Russian string.
 * Example: "8.5" → "8 ч 30 мин"
 */
export function formatHours(hours: number): string {
  return formatDuration(Math.round(hours * 60));
}

/**
 * Return the Russian day-of-week name.
 */
export function getDayOfWeekRu(date: Date | string): string {
  const d = typeof date === 'string' ? parseISO(date) : date;
  if (!isValid(d)) return '—';

  return format(d, 'EEEE', { locale: ru });
}

/**
 * Format date relative to today: "Сегодня", "Вчера", or full date.
 */
export function formatRelativeDateGroup(date: Date | string): string {
  const d = typeof date === 'string' ? parseISO(date) : date;
  if (!isValid(d)) return '—';

  const today = new Date();
  const yesterday = addDays(today, -1);

  if (isSameDay(d, today)) return 'Сегодня';
  if (isSameDay(d, yesterday)) return 'Вчера';

  return formatDateRu(d, 'd MMMM yyyy');
}

/**
 * Get ISO date string (YYYY-MM-DD) from a Date.
 */
export function toISODate(date: Date): string {
  return format(date, 'yyyy-MM-dd');
}

/**
 * Parse a YYYY-MM-DD string into a Date object at local midnight.
 */
export function parseLocalDate(dateStr: string): Date {
  return parseISO(dateStr);
}
