'use client';

import React, { useState } from 'react';
import { CalendarView, CalendarEvent } from './types';

interface CalendarGridProps {
  view: CalendarView;
  currentDate: Date;
  setCurrentDate: (date: Date) => void;
  setView: (view: CalendarView) => void;
  events: CalendarEvent[];
  onItemClick: (item: CalendarEvent) => void;
  onSlotClick: (time: Date) => void;
}

const CalendarGrid: React.FC<CalendarGridProps> = ({
  view,
  currentDate,
  setCurrentDate,
  setView,
  events,
  onItemClick,
  onSlotClick
}) => {
  const [isMonthPickerOpen, setIsMonthPickerOpen] = useState(false);
  const hours = Array.from({ length: 24 }, (_, i) => i); // Full 24 hours (0-23)
  const weekDaysShort = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];

  const formatHour = (hour: number) => {
    if (hour === 0) return '12 AM';
    if (hour === 12) return '12 PM';
    return hour > 12 ? `${hour - 12} PM` : `${hour} AM`;
  };

  const getCategoryStyles = (category: string | undefined) => {
    switch (category) {
      case 'WORK': return 'bg-black border-gray-500 text-white';
      case 'PERSONAL': return 'bg-orange-100 border-orange-500 text-black';
      case 'OTHER': return 'bg-blue-50 border-blue-400 text-black';
      default: return 'bg-gray-100 border-gray-300 text-black';
    }
  };

  const handleSlotClick = (date: Date, hour: number) => {
    const clickDate = new Date(date);
    clickDate.setHours(hour, 0, 0, 0);
    onSlotClick(clickDate);
  };

  const nextMonth = () => {
    const d = new Date(currentDate);
    d.setMonth(d.getMonth() + 1);
    setCurrentDate(d);
  };

  const prevMonth = () => {
    const d = new Date(currentDate);
    d.setMonth(d.getMonth() - 1);
    setCurrentDate(d);
  };

  const selectMonth = (monthIdx: number) => {
    const d = new Date(currentDate);
    d.setMonth(monthIdx);
    setCurrentDate(d);
    setIsMonthPickerOpen(false);
  };

  const today = new Date();

  if (view === CalendarView.MONTH) {
    const monthStart = new Date(currentDate.getFullYear(), currentDate.getMonth(), 1);
    const monthEnd = new Date(currentDate.getFullYear(), currentDate.getMonth() + 1, 0);

    let startDayOffset = monthStart.getDay() - 1;
    if (startDayOffset < 0) startDayOffset = 6;

    const days = [];
    for (let i = startDayOffset; i > 0; i--) {
      const d = new Date(monthStart);
      d.setDate(d.getDate() - i);
      days.push(d);
    }
    for (let i = 1; i <= monthEnd.getDate(); i++) {
      days.push(new Date(currentDate.getFullYear(), currentDate.getMonth(), i));
    }
    const remaining = 35 - days.length;
    const totalCells = remaining >= 0 ? 35 : 42;
    const finalRemaining = totalCells - days.length;
    for (let i = 1; i <= finalRemaining; i++) {
      const d = new Date(monthEnd);
      d.setDate(d.getDate() + i);
      days.push(d);
    }

    const monthName = currentDate.toLocaleString('en-US', { month: 'long' });
    const year = currentDate.getFullYear();

    return (
      <div className="flex flex-col bg-white border border-gray-100 rounded-[2.5rem] overflow-hidden shadow-sm h-full max-h-full">
        {/* Month Header */}
        <div className="px-8 py-5 border-b border-gray-50 flex items-center justify-between bg-white z-20 relative">
          <div className="flex items-center gap-4">
            <div className="relative">
              <button
                onClick={() => setIsMonthPickerOpen(!isMonthPickerOpen)}
                className="text-2xl font-black tracking-tighter text-black lowercase flex items-center gap-2 hover:text-orange-500 transition-colors"
              >
                {monthName} <span className="text-orange-500">{year}</span>
                <svg className={`w-4 h-4 transition-transform ${isMonthPickerOpen ? 'rotate-180' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="3" d="M19 9l-7 7-7-7" /></svg>
              </button>

              {isMonthPickerOpen && (
                <div className="absolute top-full left-0 mt-2 w-64 bg-white border border-gray-100 rounded-[2rem] shadow-2xl p-4 z-50 grid grid-cols-3 gap-2 animate-in fade-in slide-in-from-top-2">
                  {Array.from({ length: 12 }, (_, i) => (
                    <button
                      key={i}
                      onClick={() => selectMonth(i)}
                      className={`py-2 rounded-xl text-[10px] font-black uppercase tracking-tight transition-all ${
                        currentDate.getMonth() === i ? 'bg-black text-white' : 'hover:bg-gray-50 text-gray-400 hover:text-black'
                      }`}
                    >
                      {new Date(0, i).toLocaleString('en-US', { month: 'short' })}
                    </button>
                  ))}
                </div>
              )}
            </div>

            <div className="flex items-center gap-1">
              <button onClick={prevMonth} className="p-2 hover:bg-gray-100 rounded-full transition-colors text-black active:scale-90">
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" d="M15 19l-7-7 7-7" /></svg>
              </button>
              <button onClick={nextMonth} className="p-2 hover:bg-gray-100 rounded-full transition-colors text-black active:scale-90">
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" d="M9 5l7 7-7 7" /></svg>
              </button>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-1.5 h-1.5 bg-orange-500 rounded-full animate-pulse"></div>
            <span className="text-[9px] font-bold text-gray-400 uppercase tracking-widest">Active Schedule</span>
          </div>
        </div>

        <div className="grid grid-cols-7 bg-gray-50/40">
          {weekDaysShort.map(d => (
            <div key={d} className="py-2 text-center text-[9px] font-black uppercase tracking-[0.2em] text-gray-400 border-b border-gray-100/50">{d}</div>
          ))}
        </div>

        <div className={`grid grid-cols-7 flex-1 min-h-0 ${totalCells === 35 ? 'grid-rows-5' : 'grid-rows-6'}`}>
          {days.map((dateObj, i) => {
            const isToday = dateObj.toDateString() === today.toDateString();
            const isCurrentMonth = dateObj.getMonth() === currentDate.getMonth();
            const dayEvents = events.filter(e => e.startTime.toDateString() === dateObj.toDateString());
            return (
              <div
                key={i}
                className={`border-r border-b border-gray-50 transition-all hover:bg-gray-50/20 relative group p-3 cursor-pointer ${isToday ? 'bg-orange-50/20' : 'bg-white'}`}
                onClick={() => handleSlotClick(dateObj, 9)}
              >
                <span className={`text-xs font-black ${isToday ? 'text-orange-500' : isCurrentMonth ? 'text-black' : 'text-gray-200'}`}>{dateObj.getDate()}</span>
                {isToday && <div className="absolute top-3 right-3 w-1.5 h-1.5 bg-orange-500 rounded-full"></div>}
                <div className="mt-1 space-y-1 overflow-hidden">
                  {dayEvents.slice(0, 2).map(ev => (
                    <div key={ev.id} onClick={(e) => { e.stopPropagation(); onItemClick(ev); }} className="text-[7px] font-bold bg-black text-white px-1.5 py-0.5 rounded-md truncate cursor-pointer hover:bg-orange-600 transition-all">{ev.title}</div>
                  ))}
                  {dayEvents.length > 2 && (
                    <div className="text-[7px] font-bold text-gray-400">+{dayEvents.length - 2} more</div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    );
  }

  if (view === CalendarView.WEEK) {
    const dayOfWeek = currentDate.getDay();
    const startOfWeek = new Date(currentDate);
    const diff = currentDate.getDate() - dayOfWeek + (dayOfWeek === 0 ? -6 : 1);
    startOfWeek.setDate(diff);

    const weekDates = Array.from({ length: 7 }, (_, i) => {
      const d = new Date(startOfWeek);
      d.setDate(startOfWeek.getDate() + i);
      return d;
    });

    return (
      <div className="flex flex-col bg-white rounded-[2.5rem] border border-gray-100 shadow-sm h-full">
        {/* Fixed Header - Days of the week */}
        <div className="flex bg-gray-50/50 border-b border-gray-100 py-4 px-4 gap-2">
          <div className="w-16"></div>
          {weekDates.map((date, i) => {
            const isToday = date.toDateString() === today.toDateString();
            const isSelected = date.toDateString() === currentDate.toDateString();
            return (
              <div
                key={i}
                onClick={() => {
                  setCurrentDate(date);
                  setView(CalendarView.DAY);
                }}
                className={`flex-1 flex flex-col items-center py-2 px-2 rounded-full border transition-all cursor-pointer group/pill ${
                  isToday ? 'bg-orange-500 border-orange-300 text-white shadow-md' : isSelected ? 'bg-black border-black text-white shadow-md' : 'bg-white border-gray-100 text-black hover:bg-gray-50'
                }`}
              >
                <span className={`text-[8px] font-bold uppercase tracking-widest ${isToday || isSelected ? 'text-white/70' : 'text-gray-400 group-hover/pill:text-black'}`}>{weekDaysShort[i]}</span>
                <span className="text-sm font-bold">{date.getDate()}</span>
              </div>
            );
          })}
        </div>

        {/* Scrollable Time Slots - ONLY this part scrolls */}
        <div className="flex-1 overflow-y-auto" style={{ height: 'calc(100% - 80px)' }}>
          {hours.map(hour => {
            const hasEvent = events.some(e =>
              weekDates.some(wd => e.startTime.toDateString() === wd.toDateString() && e.startTime.getHours() === hour)
            );
            return (
              <div key={hour} className={`flex border-b border-gray-50 transition-all duration-300 group/row hover:bg-gray-50/10 ${hasEvent ? 'min-h-[56px]' : 'min-h-[36px]'}`}>
                <div className="w-16 flex justify-center pt-2 text-[9px] font-bold text-black uppercase sticky left-0 bg-white z-10">{formatHour(hour)}</div>
                {weekDates.map((dateObj, i) => {
                  const dayEvents = events.filter(e => e.startTime.toDateString() === dateObj.toDateString() && e.startTime.getHours() === hour);
                  return (
                    <div key={i} className="flex-1 border-l border-gray-50 relative group cursor-crosshair" onClick={() => handleSlotClick(dateObj, hour)}>
                      {dayEvents.map(ev => (
                        <div key={ev.id} onClick={(e) => { e.stopPropagation(); onItemClick(ev); }} className={`absolute inset-x-1 top-0.5 bottom-0.5 rounded-xl px-2 flex items-center shadow-sm z-10 text-[8px] font-bold cursor-pointer hover:scale-[1.01] transition-all border-l-4 truncate leading-tight ${getCategoryStyles(ev.category)}`}>
                          <span className="border border-current opacity-40 rounded-full px-1.5 py-0.5 mr-2 text-[6px] uppercase tracking-widest shrink-0 font-black">{ev.project || 'General'}</span>
                          <span className="flex-1 truncate">{ev.title}</span>
                          <span className="ml-1 opacity-50 whitespace-nowrap">&#8226; {ev.startTime.getHours()}:00</span>
                        </div>
                      ))}
                    </div>
                  );
                })}
              </div>
            );
          })}
        </div>
      </div>
    );
  }

  // DAY VIEW
  const dayEvents = events.filter(e => e.startTime.toDateString() === currentDate.toDateString());
  const sortedDayEvents = [...dayEvents].sort((a,b) => a.startTime.getTime() - b.startTime.getTime());
  const now = new Date();
  const nextUp = sortedDayEvents.find(e => e.startTime >= now) || sortedDayEvents[0];

  return (
    <div className="flex bg-white rounded-[3rem] border border-gray-100 shadow-sm h-full">
      {/* Left Panel - Header stays fixed, only time slots scroll */}
      <div className="w-2/3 flex flex-col border-r border-gray-100 h-full">
        {/* Fixed Header */}
        <div className="bg-gray-50/50 p-6 border-b border-gray-100 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="w-14 h-14 bg-black rounded-2xl flex flex-col items-center justify-center text-white">
              <span className="text-[8px] font-black uppercase mb-1">{currentDate.toLocaleDateString('en-US', { weekday: 'short' })}</span>
              <span className="text-xl font-black">{currentDate.getDate()}</span>
            </div>
            <div>
              <h3 className="text-lg font-bold text-black">Today&apos;s Schedule</h3>
              <p className="text-[10px] text-gray-400 font-bold uppercase tracking-widest">{currentDate.toLocaleString('en-US', { month: 'long', year: 'numeric' })}</p>
            </div>
          </div>
        </div>

        {/* Scrollable Time Slots - ONLY this part scrolls */}
        <div className="flex-1 overflow-y-auto scroll-smooth" style={{ height: 'calc(100% - 100px)' }}>
          {hours.map(hour => {
            const hourEvents = dayEvents.filter(e => e.startTime.getHours() === hour);
            const hasEvent = hourEvents.length > 0;
            return (
              <div key={hour} className={`flex border-b border-gray-50 transition-all duration-300 group ${hasEvent ? 'min-h-[64px]' : 'min-h-[44px]'}`}>
                <div className="w-20 flex justify-center pt-3 text-[10px] font-bold text-black uppercase tracking-tighter">{formatHour(hour)}</div>
                <div className="flex-1 border-l border-gray-100 p-2 relative cursor-crosshair hover:bg-gray-50/50 transition-colors" onClick={() => handleSlotClick(currentDate, hour)}>
                  {hourEvents.map(event => (
                     <div key={event.id} onClick={(e) => { e.stopPropagation(); onItemClick(event); }} className={`absolute inset-x-2 top-1 bottom-1 rounded-2xl px-4 flex items-center shadow-md z-10 cursor-pointer hover:scale-[1.01] transition-all border-l-[6px] ${getCategoryStyles(event.category)}`}>
                       <div className="flex items-center gap-2 w-full truncate">
                         <span className="border border-current opacity-40 rounded-full px-2 py-0.5 text-[8px] uppercase tracking-widest shrink-0 font-black">{event.project || 'General'}</span>
                         <h4 className="font-bold text-sm truncate flex-1">{event.title}</h4>
                         <span className="text-[9px] font-black opacity-40">{event.startTime.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                       </div>
                    </div>
                  ))}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Right Panel - Completely fixed, no scrolling */}
      <div className="w-1/3 bg-gray-50/30 p-8 overflow-hidden">
        <div className="mb-10">
          <h4 className="text-[10px] font-black uppercase tracking-[0.3em] text-orange-500 mb-6">Next Event</h4>
          {nextUp ? (
            <div className="bg-white rounded-[2.5rem] p-8 border border-gray-100 shadow-xl shadow-black/5 animate-in fade-in slide-in-from-right-4 duration-500">
              <div className={`w-12 h-1.5 rounded-full mb-6 ${getCategoryStyles(nextUp.category).split(' ')[0]}`}></div>
              <h2 className="text-2xl font-black text-black leading-tight mb-2">{nextUp.title}</h2>
              <div className="flex items-center gap-2 mb-6">
                <div className="w-1.5 h-1.5 bg-green-500 rounded-full animate-pulse"></div>
                <span className="text-[10px] font-bold text-gray-400 uppercase tracking-widest">Upcoming</span>
              </div>
              <div className="space-y-4 mb-8">
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-xl bg-gray-100 flex items-center justify-center shrink-0">
                    <svg className="w-4 h-4 text-black" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
                  </div>
                  <div>
                    <p className="text-[8px] font-black text-gray-400 uppercase">Time</p>
                    <p className="text-xs font-bold text-black">{nextUp.startTime.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })} - {nextUp.endTime.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</p>
                  </div>
                </div>
                {nextUp.project && (
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-xl bg-gray-100 flex items-center justify-center shrink-0">
                      <svg className="w-4 h-4 text-black" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" /></svg>
                    </div>
                    <div>
                      <p className="text-[8px] font-black text-gray-400 uppercase">Project</p>
                      <p className="text-xs font-bold text-black">{nextUp.project}</p>
                    </div>
                  </div>
                )}
              </div>
              <button onClick={() => onItemClick(nextUp)} className="w-full bg-black text-white py-4 rounded-full text-[10px] font-black uppercase tracking-[0.2em] hover:bg-orange-500 transition-all active:scale-95 shadow-lg shadow-black/10">View full details</button>
            </div>
          ) : (
            <div className="bg-white/50 border border-dashed border-gray-200 rounded-[2.5rem] p-8 text-center">
              <p className="text-sm font-bold text-gray-400 italic">Clear skies ahead for today.</p>
              <p className="mt-2 text-[9px] text-gray-300">Click any time slot to add an event</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default CalendarGrid;
