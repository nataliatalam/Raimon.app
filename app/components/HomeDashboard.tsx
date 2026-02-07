'use client';

import React, { useEffect, useMemo, useState } from 'react';
import { ArrowRight, Calendar as CalendarIcon, Sparkles, Target } from 'lucide-react';
import MicroLabel from './ui/MicroLabel';
import SystemGuide from './SystemGuide';
import StreakWidget from './StreakWidget';
import type { CalendarEvent } from './calendar/types';

type HomeDashboardProps = {
  userName?: string;
  streakCount: number;
  projectFilterControl: React.ReactNode;
  onStartDoing: () => void;
  onOpenCalendar: () => void;
  nextEvent?: CalendarEvent | null;
};

const formatTimeRange = (event: CalendarEvent) => {
  const start = event.startTime.toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' });
  const end = event.endTime.toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' });
  return `${start} – ${end}`;
};

const HomeDashboard: React.FC<HomeDashboardProps> = ({
  userName,
  streakCount,
  projectFilterControl,
  onStartDoing,
  onOpenCalendar,
  nextEvent,
}) => {
  const [showGuide, setShowGuide] = useState(false);
  const [currentTime, setCurrentTime] = useState(() => new Date());

  useEffect(() => {
    const interval = setInterval(() => setCurrentTime(new Date()), 60 * 1000);
    return () => clearInterval(interval);
  }, []);

  const greeting = useMemo(() => {
    const hour = currentTime.getHours();
    if (hour < 12) return 'Good Morning';
    if (hour < 18) return 'Good Afternoon';
    return 'Good Evening';
  }, [currentTime]);

  const formattedDate = useMemo(
    () => currentTime.toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric' }),
    [currentTime]
  );

  const formattedTime = useMemo(
    () => currentTime.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' }),
    [currentTime]
  );

  const nextEventLabel = nextEvent
    ? {
        day: nextEvent.startTime.toLocaleDateString('en-US', { weekday: 'long' }),
        time: formatTimeRange(nextEvent),
        title: nextEvent.title,
        subtitle: nextEvent.project ?? 'General',
      }
    : null;

  return (
    <div className="h-full w-full flex flex-col p-8 lg:p-12 animate-in fade-in slide-in-from-bottom-4 duration-700 overflow-y-auto custom-scrollbar">
      <div className="flex flex-col gap-8 mb-12">
        <div className="flex justify-between items-start gap-6 flex-wrap">
          <div className="flex flex-col gap-2">
            <div className="flex items-center gap-3 text-[#FF6B00]">
              <span className="text-xs font-black uppercase tracking-[0.3em]">{formattedDate}</span>
              <div className="h-px w-10 bg-[#FF6B00]/40" />
            </div>
            <h1 className="text-5xl font-black tracking-tight leading-none text-black">
              {greeting}
              <span className="text-[#FF6B00]">.</span>
            </h1>
            <p className="text-lg text-zinc-500 font-medium">Let&apos;s build momentum, {userName ?? 'friend'}.</p>
          </div>
          <div className="flex flex-col items-end gap-3">
            <StreakWidget streakCount={streakCount} />
            <button
              type="button"
              onClick={() => setShowGuide(true)}
              className="text-[10px] font-black uppercase tracking-[0.3em] text-[#FF6B00] hover:text-black transition-colors"
            >
              How Raimon Works
            </button>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-12 gap-8 mb-16">
        <div className="col-span-12 lg:col-span-8 bg-black rounded-[3.5rem] p-12 lg:p-16 flex flex-col relative overflow-hidden group shadow-[0_40px_100px_rgba(0,0,0,0.2)]">
          <div className="relative z-10 flex flex-col h-full">
            <MicroLabel text="THE PERFECT NEXT STEP" color="text-[#FF6B00]" />
            <div className="mt-8 flex flex-col gap-4 items-start">
              <MicroLabel text="CURRENT CONTEXT" color="text-white/40" />
              {projectFilterControl}
            </div>
            <div className="mt-16 lg:mt-24 flex items-center gap-6 flex-wrap">
              <button
                type="button"
                onClick={onStartDoing}
                className="px-12 py-6 bg-[#FF6B00] text-white rounded-full font-black text-[11px] uppercase tracking-[0.4em] flex items-center gap-4 hover:bg-white hover:text-black transition-all shadow-2xl shadow-[#FF6B00]/40 active:scale-95 group/start"
              >
                Start Doing
                <ArrowRight size={18} className="group-hover/start:translate-x-1 transition-transform" />
              </button>
              <div className="text-white/40 text-[10px] font-black uppercase tracking-widest">
                Ready for focus
              </div>
            </div>
          </div>
          <div className="absolute -right-20 -bottom-20 opacity-[0.03] group-hover:opacity-[0.06] group-hover:scale-110 transition-all duration-1000 text-white pointer-events-none">
            <Target size={400} strokeWidth={0.5} />
          </div>
        </div>

        <div className="col-span-12 lg:col-span-4 flex flex-col gap-8">
          <button
            type="button"
            onClick={onOpenCalendar}
            className="bg-white rounded-[3rem] p-10 border border-zinc-100 shadow-sm flex flex-col group hover:shadow-xl transition-all duration-500 text-left"
          >
            <div className="flex items-center justify-between mb-8">
              <MicroLabel text="NEXT EVENT" color="text-zinc-400" />
              <CalendarIcon size={18} className="text-zinc-300 group-hover:text-[#FF6B00] transition-colors" />
            </div>
            {nextEventLabel ? (
              <>
                <p className="text-sm font-black text-[#FF6B00] uppercase tracking-widest">
                  {nextEventLabel.day} @ {nextEventLabel.time}
                </p>
                <h3 className="text-2xl font-black text-black tracking-tight uppercase leading-none mt-2">
                  {nextEventLabel.title}
                </h3>
                <p className="text-zinc-400 font-medium mt-3">{nextEventLabel.subtitle}</p>
              </>
            ) : (
              <p className="text-zinc-500 font-medium">No events on deck. Add one from your calendar.</p>
            )}
          </button>

          <div className="bg-zinc-900 rounded-[3rem] p-10 flex flex-col shadow-2xl relative overflow-hidden group">
            <MicroLabel text="SYSTEM TIME" color="text-white/40" />
            <div className="text-5xl font-light text-white tracking-tighter mt-4 leading-none tabular-nums">
              {formattedTime}
            </div>
            <div className="absolute right-[-20%] bottom-[-20%] opacity-5 text-white pointer-events-none transition-transform group-hover:rotate-12 duration-700">
              <Sparkles size={160} />
            </div>
          </div>
        </div>
      </div>

      {showGuide && <SystemGuide onClose={() => setShowGuide(false)} />}
    </div>
  );
};

export default HomeDashboard;
