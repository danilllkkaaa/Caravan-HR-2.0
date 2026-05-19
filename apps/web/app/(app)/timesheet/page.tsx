'use client';

import { useState } from 'react';
import { ChevronLeft, ChevronRight, Clock, Sun, Coffee } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { format, startOfMonth, endOfMonth, eachDayOfInterval, getDay, isSameDay, isToday } from 'date-fns';
import { ru } from 'date-fns/locale';
import { timesheetApi } from '@/lib/api/timesheet';
import { TimesheetStatus } from '@corp-portal/shared-types';
import type { TimesheetEntry } from '@corp-portal/shared-types';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { formatTime, formatHours } from '@corp-portal/ui-core';
import clsx from 'clsx';

const STATUS_COLORS: Record<TimesheetStatus, string> = {
  [TimesheetStatus.Work]: 'bg-success-100 text-success-700 border-success-200',
  [TimesheetStatus.Overtime]: 'bg-accent-100 text-accent-700 border-accent-200',
  [TimesheetStatus.Partial]: 'bg-orange-100 text-orange-700 border-orange-200',
  [TimesheetStatus.Absence]: 'bg-danger-100 text-danger-700 border-danger-200',
  [TimesheetStatus.Holiday]: 'bg-purple-100 text-purple-700 border-purple-200',
  [TimesheetStatus.Weekend]: 'bg-gray-100 text-gray-400 border-gray-200',
  [TimesheetStatus.Vacation]: 'bg-blue-100 text-blue-700 border-blue-200',
  [TimesheetStatus.Sick]: 'bg-warning-100 text-warning-700 border-warning-200',
};

const STATUS_LABELS: Record<TimesheetStatus, string> = {
  [TimesheetStatus.Work]: 'На работе',
  [TimesheetStatus.Overtime]: 'Сверхурочно',
  [TimesheetStatus.Partial]: 'Неполный день',
  [TimesheetStatus.Absence]: 'Отсутствие',
  [TimesheetStatus.Holiday]: 'Праздник',
  [TimesheetStatus.Weekend]: 'Выходной',
  [TimesheetStatus.Vacation]: 'Отпуск',
  [TimesheetStatus.Sick]: 'Больничный',
};

const WEEKDAY_LABELS = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс'];

function DayCell({
  date,
  entry,
  isSelected,
  onClick,
}: {
  date: Date;
  entry?: TimesheetEntry;
  isSelected: boolean;
  onClick: () => void;
}) {
  const dayOfWeek = getDay(date);
  const isWeekendDay = dayOfWeek === 0 || dayOfWeek === 6;
  const isTodayDate = isToday(date);

  const statusClass = entry
    ? STATUS_COLORS[entry.status]
    : isWeekendDay
    ? 'bg-gray-50 text-gray-300 border-gray-100'
    : 'bg-white text-gray-500 border-gray-100 hover:bg-gray-50';

  return (
    <button
      onClick={onClick}
      className={clsx(
        'aspect-square rounded-xl border text-xs font-medium flex flex-col items-center justify-center transition-all',
        statusClass,
        isTodayDate && 'ring-2 ring-primary-800 ring-offset-1',
        isSelected && 'ring-2 ring-accent-500 ring-offset-1 shadow-md'
      )}
    >
      <span className={clsx('text-sm font-bold', isTodayDate && 'underline underline-offset-2')}>
        {format(date, 'd')}
      </span>
      {entry && entry.hoursWorked != null && (
        <span className="text-[9px] mt-0.5 opacity-75">
          {entry.hoursWorked.toFixed(0)}ч
        </span>
      )}
    </button>
  );
}

function DayDetailSheet({
  date,
  entry,
  onClose,
}: {
  date: Date;
  entry?: TimesheetEntry;
  onClose: () => void;
}) {
  return (
    <div className="fixed inset-0 z-50 flex items-end justify-center" onClick={onClose}>
      <div className="absolute inset-0 bg-black/30 backdrop-blur-sm" />
      <div
        className="relative bg-white rounded-t-3xl w-full max-w-lg px-6 py-6 pb-safe-bottom animate-slide-up"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Handle */}
        <div className="w-10 h-1 rounded-full bg-gray-200 mx-auto mb-5" />

        <h3 className="text-lg font-bold text-gray-900 mb-1">
          {format(date, 'EEEE, d MMMM', { locale: ru }).replace(/^./, (c) => c.toUpperCase())}
        </h3>

        {entry ? (
          <div className="space-y-4 mt-4">
            <div
              className={clsx(
                'inline-flex items-center gap-2 px-3 py-1.5 rounded-full text-sm font-medium border',
                STATUS_COLORS[entry.status]
              )}
            >
              {STATUS_LABELS[entry.status]}
            </div>

            <div className="grid grid-cols-2 gap-3">
              {entry.checkIn && (
                <div className="bg-gray-50 rounded-xl p-3">
                  <p className="text-xs text-gray-500">Приход</p>
                  <p className="text-lg font-bold text-gray-900">{formatTime(entry.checkIn)}</p>
                </div>
              )}
              {entry.checkOut && (
                <div className="bg-gray-50 rounded-xl p-3">
                  <p className="text-xs text-gray-500">Уход</p>
                  <p className="text-lg font-bold text-gray-900">{formatTime(entry.checkOut)}</p>
                </div>
              )}
              {entry.hoursWorked != null && (
                <div className="bg-gray-50 rounded-xl p-3">
                  <p className="text-xs text-gray-500">Отработано</p>
                  <p className="text-lg font-bold text-gray-900">{formatHours(entry.hoursWorked)}</p>
                </div>
              )}
              {entry.overtimeHours != null && entry.overtimeHours > 0 && (
                <div className="bg-warning-50 rounded-xl p-3">
                  <p className="text-xs text-warning-600">Сверхурочно</p>
                  <p className="text-lg font-bold text-warning-800">{formatHours(entry.overtimeHours)}</p>
                </div>
              )}
            </div>

            {entry.location && (
              <div className="flex items-center gap-2 text-sm text-gray-600">
                <Sun className="w-4 h-4 text-gray-400" />
                {entry.location.name}
              </div>
            )}

            {entry.note && (
              <p className="text-sm text-gray-500 italic">{entry.note}</p>
            )}
          </div>
        ) : (
          <div className="text-center py-8">
            <Coffee className="w-10 h-10 text-gray-300 mx-auto mb-3" />
            <p className="text-gray-500 text-sm">Нет данных за этот день</p>
          </div>
        )}

        <button
          onClick={onClose}
          className="mt-5 w-full py-2.5 rounded-xl bg-gray-100 text-sm font-medium text-gray-700 hover:bg-gray-200 transition-colors"
        >
          Закрыть
        </button>
      </div>
    </div>
  );
}

export default function TimesheetPage() {
  const [currentDate, setCurrentDate] = useState(new Date());
  const [selectedDate, setSelectedDate] = useState<Date | null>(null);

  const year = currentDate.getFullYear();
  const month = currentDate.getMonth() + 1;

  const { data, isLoading } = useQuery({
    queryKey: ['timesheet', year, month],
    queryFn: () => timesheetApi.getMonth(year, month),
  });

  const daysInMonth = eachDayOfInterval({
    start: startOfMonth(currentDate),
    end: endOfMonth(currentDate),
  });

  // Padding for calendar grid (Monday start)
  const firstDayOfWeek = (getDay(daysInMonth[0]!) + 6) % 7;
  const paddingDays = Array.from({ length: firstDayOfWeek });

  const entriesByDate = (data?.entries ?? []).reduce<Record<string, TimesheetEntry>>(
    (acc, entry) => {
      acc[entry.date] = entry;
      return acc;
    },
    {}
  );

  const summary = data?.summary;
  const selectedEntry = selectedDate
    ? entriesByDate[format(selectedDate, 'yyyy-MM-dd')]
    : undefined;

  const prevMonth = () =>
    setCurrentDate((d) => new Date(d.getFullYear(), d.getMonth() - 1, 1));
  const nextMonth = () =>
    setCurrentDate((d) => new Date(d.getFullYear(), d.getMonth() + 1, 1));

  return (
    <div className="space-y-5">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Табель</h1>
        <p className="text-gray-500 text-sm mt-0.5">Учёт рабочего времени</p>
      </div>

      {/* Month navigation */}
      <div className="flex items-center justify-between bg-white rounded-2xl shadow-card px-4 py-3">
        <button
          onClick={prevMonth}
          className="w-8 h-8 flex items-center justify-center rounded-lg hover:bg-gray-100 transition-colors"
        >
          <ChevronLeft className="w-5 h-5 text-gray-600" />
        </button>
        <h2 className="text-base font-semibold text-gray-900">
          {format(currentDate, 'LLLL yyyy', { locale: ru }).replace(/^./, (c) => c.toUpperCase())}
        </h2>
        <button
          onClick={nextMonth}
          className="w-8 h-8 flex items-center justify-center rounded-lg hover:bg-gray-100 transition-colors"
          disabled={
            currentDate.getFullYear() === new Date().getFullYear() &&
            currentDate.getMonth() === new Date().getMonth()
          }
        >
          <ChevronRight className="w-5 h-5 text-gray-600" />
        </button>
      </div>

      {/* Summary header */}
      {summary && (
        <div className="grid grid-cols-3 sm:grid-cols-6 gap-2">
          {[
            { label: 'Присутствий', value: summary.presentDays, color: 'text-success-600' },
            { label: 'Отпуск', value: summary.vacationDays, color: 'text-blue-600' },
            { label: 'Б/листов', value: summary.sickLeaveDays, color: 'text-warning-600' },
            { label: 'Отсутствий', value: summary.absentDays, color: 'text-danger-600' },
            { label: 'Праздников', value: summary.holidayDays, color: 'text-purple-600' },
            {
              label: 'Часов',
              value: `${summary.totalHoursWorked.toFixed(0)}`,
              color: 'text-gray-900',
            },
          ].map((item) => (
            <div key={item.label} className="bg-white rounded-xl shadow-card px-3 py-2.5 text-center">
              <p className={clsx('text-lg font-bold', item.color)}>{item.value}</p>
              <p className="text-[10px] text-gray-400 mt-0.5">{item.label}</p>
            </div>
          ))}
        </div>
      )}

      {/* Calendar */}
      {isLoading ? (
        <div className="flex justify-center py-12">
          <LoadingSpinner size="lg" />
        </div>
      ) : (
        <div className="bg-white rounded-2xl shadow-card p-4">
          {/* Weekday headers */}
          <div className="grid grid-cols-7 gap-1 mb-2">
            {WEEKDAY_LABELS.map((day) => (
              <div
                key={day}
                className={clsx(
                  'text-center text-xs font-semibold py-1',
                  day === 'Сб' || day === 'Вс' ? 'text-danger-400' : 'text-gray-400'
                )}
              >
                {day}
              </div>
            ))}
          </div>

          {/* Day cells */}
          <div className="grid grid-cols-7 gap-1">
            {paddingDays.map((_, i) => (
              <div key={`pad-${i}`} />
            ))}
            {daysInMonth.map((date) => {
              const dateStr = format(date, 'yyyy-MM-dd');
              const entry = entriesByDate[dateStr];
              return (
                <DayCell
                  key={dateStr}
                  date={date}
                  entry={entry}
                  isSelected={selectedDate ? isSameDay(date, selectedDate) : false}
                  onClick={() =>
                    setSelectedDate(
                      selectedDate && isSameDay(date, selectedDate) ? null : date
                    )
                  }
                />
              );
            })}
          </div>

          {/* Legend */}
          <div className="mt-4 pt-4 border-t border-gray-50 flex flex-wrap gap-2">
            {[
              { status: TimesheetStatus.Work, label: 'Работа' },
              { status: TimesheetStatus.Overtime, label: 'Сверхурочно' },
              { status: TimesheetStatus.Vacation, label: 'Отпуск' },
              { status: TimesheetStatus.Sick, label: 'Больничный' },
              { status: TimesheetStatus.Holiday, label: 'Праздник' },
            ].map(({ status, label }) => (
              <div key={status} className="flex items-center gap-1.5">
                <div className={clsx('w-3 h-3 rounded border', STATUS_COLORS[status])} />
                <span className="text-xs text-gray-500">{label}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Day detail bottom sheet */}
      {selectedDate && (
        <DayDetailSheet
          date={selectedDate}
          entry={selectedEntry}
          onClose={() => setSelectedDate(null)}
        />
      )}
    </div>
  );
}
