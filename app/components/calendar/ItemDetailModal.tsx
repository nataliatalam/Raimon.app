'use client';

import React, { useState, useEffect, useRef } from 'react';
import { CalendarEvent, CalendarProject } from './types';

interface ItemDetailModalProps {
  item: CalendarEvent | null;
  isNew?: boolean;
  onClose: () => void;
  onSave: (updatedItem: CalendarEvent) => void;
  onDelete: (id: string) => void;
  projects: CalendarProject[];
}

const ItemDetailModal: React.FC<ItemDetailModalProps> = ({ item, isNew, onClose, onSave, onDelete, projects }) => {
  const [title, setTitle] = useState('');
  const [projectName, setProjectName] = useState('Other');
  const [date, setDate] = useState('');
  const [startTime, setStartTime] = useState('09:00');
  const [endTime, setEndTime] = useState('10:00');
  const [duration, setDuration] = useState<number>(60);
  const [isProjectDropdownOpen, setIsProjectDropdownOpen] = useState(false);

  const dropdownRef = useRef<HTMLDivElement>(null);
  const dateRef = useRef<HTMLInputElement>(null);
  const startRef = useRef<HTMLInputElement>(null);
  const endRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (item) {
      setTitle(item.title || '');
      setProjectName(item.project || 'Other');
      // Use local date format to avoid timezone issues
      const year = item.startTime.getFullYear();
      const month = String(item.startTime.getMonth() + 1).padStart(2, '0');
      const day = String(item.startTime.getDate()).padStart(2, '0');
      setDate(`${year}-${month}-${day}`);
      setStartTime(item.startTime.toTimeString().slice(0, 5));
      setEndTime(item.endTime.toTimeString().slice(0, 5));
      const diff = (item.endTime.getTime() - item.startTime.getTime()) / (1000 * 60);
      setDuration(Math.round(diff));
    }
  }, [item]);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsProjectDropdownOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  if (!item) return null;

  const handleDurationChange = (mins: number) => {
    setDuration(mins);
    if (startTime) {
      const [h, m] = startTime.split(':').map(Number);
      const end = new Date();
      end.setHours(h, m + mins);
      setEndTime(end.toTimeString().slice(0, 5));
    }
  };

  const handleFinalSave = () => {
    const currentProject = projects.find(p => p.name === projectName);
    const category = currentProject?.category || 'OTHER';

    const [y, mon, d] = date.split('-').map(Number);
    const [sh, sm] = startTime.split(':').map(Number);
    const [eh, em] = endTime.split(':').map(Number);

    const sDate = new Date(y, mon - 1, d, sh, sm);
    const eDate = new Date(y, mon - 1, d, eh, em);

    const updated: CalendarEvent = {
      ...item,
      title: title || 'New Event',
      project: projectName,
      projectId: currentProject?.id,
      category,
      startTime: sDate,
      endTime: eDate,
    };

    onSave(updated);
  };

  // Build project options: user projects + Other
  const projectOptions: CalendarProject[] = [
    ...projects,
    { id: 'other', name: 'Other', category: 'OTHER' }
  ];

  const selectedProject = projectOptions.find(p => p.name === projectName) || { id: 'other', name: 'Other', category: 'OTHER' as const };
  // Parse date as local time to avoid timezone issues
  const [year, month, day] = date.split('-').map(Number);
  const formattedDate = new Date(year, month - 1, day);
  const weekday = formattedDate.toLocaleDateString('en-US', { weekday: 'short' });
  const dayMonth = formattedDate.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });

  const triggerPicker = (ref: React.RefObject<HTMLInputElement | null>) => {
    if (ref.current) {
      try {
        if ('showPicker' in HTMLInputElement.prototype) {
          ref.current.showPicker();
        } else {
          ref.current.click();
        }
      } catch {
        ref.current.click();
      }
    }
  };

  const getCategoryColor = (category: string) => {
    switch (category) {
      case 'WORK': return 'bg-black';
      case 'PERSONAL': return 'bg-orange-500';
      case 'OTHER': return 'bg-blue-400';
      default: return 'bg-gray-400';
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40 backdrop-blur-sm animate-in fade-in duration-300">
      <div className="bg-white w-full max-w-[380px] rounded-[3rem] shadow-2xl animate-in zoom-in-95 duration-200 overflow-hidden px-8 py-6">
        <div className="flex justify-end mb-1">
          <button onClick={onClose} className="p-1 text-gray-400 hover:text-black transition-all">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="3" d="M6 18L18 6M6 6l12 12" /></svg>
          </button>
        </div>

        <div className="space-y-4">
          {/* Goal Input - Blue Border */}
          <div className="px-2">
             <input
              className="text-center text-lg font-bold text-black bg-white border-2 border-[#1a73e8] rounded-lg focus:ring-0 px-4 py-1.5 w-full placeholder:text-gray-200 transition-all shadow-sm"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="New Event"
              autoFocus
            />
          </div>

          {/* Date Container - Matches Image */}
          <div className="relative group flex justify-center cursor-pointer px-2" onClick={() => triggerPicker(dateRef)}>
            <input
              ref={dateRef}
              type="date"
              value={date}
              onChange={(e) => setDate(e.target.value)}
              className="opacity-0 absolute inset-0 cursor-pointer pointer-events-none w-full h-full"
            />
            <div className="w-full border border-dashed border-gray-100 py-6 px-4 rounded-[2rem] text-center group-hover:bg-gray-50/50 group-hover:border-orange-200 transition-all">
              <span className="text-[10px] font-black uppercase tracking-[0.25em] text-[#FF6B00] block mb-0.5">{weekday}</span>
              <span className="text-4xl font-black text-black tracking-tight">{dayMonth}</span>
            </div>
          </div>

          {/* Time containers - Side by side (Clickable) */}
          <div className="flex gap-3 px-2">
            <div className="flex-1 relative group cursor-pointer" onClick={() => triggerPicker(startRef)}>
              <input
                ref={startRef}
                type="time"
                value={startTime}
                onChange={(e) => setStartTime(e.target.value)}
                className="opacity-0 absolute inset-0 cursor-pointer pointer-events-none w-full h-full"
              />
              <div className="border border-dashed border-gray-100 py-4 px-2 rounded-[1.8rem] text-center group-hover:bg-gray-50/50 group-hover:border-orange-200 transition-all">
                <span className="text-[9px] font-bold uppercase text-gray-300 tracking-tight block mb-0.5">START TIME</span>
                <span className="text-3xl font-black text-black leading-none">{startTime}</span>
              </div>
            </div>
            <div className="flex-1 relative group cursor-pointer" onClick={() => triggerPicker(endRef)}>
              <input
                ref={endRef}
                type="time"
                value={endTime}
                onChange={(e) => setEndTime(e.target.value)}
                className="opacity-0 absolute inset-0 cursor-pointer pointer-events-none w-full h-full"
              />
              <div className="border border-dashed border-gray-100 py-4 px-2 rounded-[1.8rem] text-center group-hover:bg-gray-50/50 group-hover:border-orange-200 transition-all">
                <span className="text-[9px] font-bold uppercase text-gray-300 tracking-tight block mb-0.5">END TIME</span>
                <span className="text-3xl font-black text-black leading-none">{endTime}</span>
              </div>
            </div>
          </div>

          {/* Duration Selector - Matches Image Style */}
          <div className="bg-[#f8f9fa] p-1.5 rounded-full flex gap-1 items-center mx-2">
            {[15, 30, 60, 120].map(mins => (
              <button
                key={mins}
                onClick={() => handleDurationChange(mins)}
                className={`flex-1 py-3 rounded-full flex flex-col items-center justify-center transition-all ${
                  duration === mins
                    ? 'bg-white text-black shadow-lg shadow-black/5 scale-[1.02]'
                    : 'text-gray-300 hover:text-gray-400'
                }`}
              >
                <span className="text-sm font-black leading-none">{mins}</span>
                <span className="text-[7px] font-bold uppercase mt-0.5">MIN</span>
              </button>
            ))}
          </div>

          {/* Category Dropdown - User Projects + Other */}
          <div className="relative px-2" ref={dropdownRef}>
            <button
              onClick={() => setIsProjectDropdownOpen(!isProjectDropdownOpen)}
              className="w-full flex items-center justify-between border border-gray-100 bg-white px-5 py-3.5 rounded-full text-xs font-bold text-black hover:border-gray-200 transition-all shadow-sm"
            >
              <div className="flex items-center gap-3">
                <div className={`w-3 h-3 rounded-full ${getCategoryColor(selectedProject.category)}`}></div>
                <span>{projectName}</span>
              </div>
              <svg className={`w-4 h-4 text-gray-300 transition-transform ${isProjectDropdownOpen ? 'rotate-180' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" d="M19 9l-7 7-7-7" /></svg>
            </button>

            {isProjectDropdownOpen && (
              <div className="absolute bottom-full left-2 right-2 mb-2 bg-white border border-gray-100 rounded-[2rem] shadow-2xl z-50 py-2 animate-in slide-in-from-bottom-2 max-h-[200px] overflow-y-auto">
                {projectOptions.map(p => (
                  <button
                    key={p.id}
                    onClick={() => {
                      setProjectName(p.name);
                      setIsProjectDropdownOpen(false);
                    }}
                    className="w-full text-left px-6 py-3 hover:bg-gray-50 flex items-center gap-4 transition-colors"
                  >
                    <div className={`w-2.5 h-2.5 rounded-full ${getCategoryColor(p.category)}`}></div>
                    <span className="text-xs font-bold text-gray-700">{p.name}</span>
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Action Button */}
          <div className="pt-2 flex flex-col items-center">
            <button
              onClick={handleFinalSave}
              className="w-full bg-black text-white py-4 rounded-full text-xs font-black uppercase tracking-[0.4em] shadow-xl hover:bg-gray-900 transition-all active:scale-95 mb-4"
            >
              {isNew ? 'ADD' : 'SAVE'}
            </button>

            {!isNew && item.id && (
              <button
                onClick={() => onDelete(item.id)}
                className="text-[#FFC7C7] text-[10px] font-black uppercase tracking-[0.2em] hover:text-[#FF8E8E] transition-all"
              >
                DISCARD
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default ItemDetailModal;
