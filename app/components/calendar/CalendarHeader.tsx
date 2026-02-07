'use client';

import React from 'react';
import { CalendarView } from './types';

interface CalendarHeaderProps {
  currentView: CalendarView;
  setView: (view: CalendarView) => void;
  onOpenGuide: () => void;
}

const CalendarHeader: React.FC<CalendarHeaderProps> = ({ currentView, setView, onOpenGuide }) => {
  return (
    <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6 mb-8">
      {/* Title Area */}
      <div className="flex items-baseline gap-2">
        <h1 className="text-4xl font-light text-black tracking-tight">My <span className="text-orange-500 font-semibold">Calendar</span></h1>
      </div>

      {/* Center: Fully Rounded Pill View Switcher */}
      <div className="flex items-center bg-gray-100/80 backdrop-blur-md p-1.5 rounded-full border border-gray-200 shadow-inner">
        {[CalendarView.DAY, CalendarView.WEEK, CalendarView.MONTH].map((view) => (
          <button
            key={view}
            onClick={() => setView(view)}
            className={`px-6 py-2.5 rounded-full text-[10px] font-black uppercase tracking-[0.2em] transition-all duration-500 ease-out flex items-center justify-center min-w-[100px] ${
              currentView === view
                ? 'bg-black text-white shadow-xl shadow-black/20 scale-105 z-10'
                : 'text-gray-400 hover:text-black hover:bg-white/50'
            }`}
          >
            {view}
          </button>
        ))}
      </div>

      {/* Right: Guide */}
      <div className="flex items-center gap-3">
        <button
          onClick={onOpenGuide}
          className="h-10 px-6 rounded-full bg-white text-black flex items-center gap-2 hover:bg-orange-500 hover:text-white transition-all active:scale-95 group border border-gray-100 shadow-sm"
        >
          <div className="w-4 h-4 bg-black group-hover:bg-white rounded-full flex items-center justify-center transition-colors">
            <span className="text-[8px] font-black text-white group-hover:text-black">?</span>
          </div>
          <span className="text-[9px] font-black uppercase tracking-[0.1em]">How it works</span>
        </button>
      </div>
    </div>
  );
};

export default CalendarHeader;
