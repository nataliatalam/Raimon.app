'use client';

import React, { useState } from 'react';
import { ArrowLeft, Wind, Droplets, Coffee, MessageSquare, User, Ghost, Heart, Cookie, Timer, Eye, Phone, Moon, Frown, ShoppingBag, Lock, Plus } from 'lucide-react';
import MicroLabel from './ui/MicroLabel';
import BrainDump from './BrainDump';

interface OxygenRoomProps {
  onReturn: () => void;
}

const REST_MODES = [
  { id: 'water', label: 'Water Refill', icon: <Droplets size={16} />, color: 'bg-[#93C5FD] text-[#1E3A8A]', border: 'border-[#1E3A8A]' },
  { id: 'coffee', label: 'Coffee Run', icon: <Coffee size={16} />, color: 'bg-[#FDE68A] text-[#78350F]', border: 'border-[#78350F]' },
  { id: 'colleague', label: "Colleagues life story", icon: <MessageSquare size={16} />, color: 'bg-[#D1FAE5] text-[#065F46]', border: 'border-[#065F46]' },
  { id: 'call', label: "took a call", icon: <Phone size={16} />, color: 'bg-blue-50 text-blue-900', border: 'border-blue-200' },
  { id: 'restroom', label: 'restroom', icon: <User size={16} />, color: 'bg-[#FBCFE8] text-[#831843]', border: 'border-[#831843]' },
  { id: 'crying', label: 'crying in restroom', icon: <Ghost size={16} />, color: 'bg-[#E9D5FF] text-[#581C87]', border: 'border-[#581C87]' },
  { id: 'poop', label: 'took a dump', icon: <Timer size={16} />, color: 'bg-[#D97706] text-[#451A03]', border: 'border-[#451A03]' },
  { id: 'got_dumped', label: 'got dumped', icon: <Frown size={16} />, color: 'bg-zinc-200 text-zinc-900', border: 'border-zinc-300' },
  { id: 'milk', label: 'milk run', icon: <ShoppingBag size={16} />, color: 'bg-zinc-100 text-zinc-900', border: 'border-zinc-300' },
  { id: 'nap', label: 'took a nap', icon: <Moon size={16} />, color: 'bg-indigo-900 text-indigo-50', border: 'border-indigo-700' },
  { id: 'makeout', label: 'make out sesh', icon: <Heart size={16} />, color: 'bg-[#FCA5A5] text-[#7F1D1D]', border: 'border-[#7F1D1D]' },
  { id: 'snack', label: 'got a lil snack', icon: <Cookie size={16} />, color: 'bg-[#FCD34D] text-[#78350F]', border: 'border-[#78350F]' },
  { id: 'mystery', label: 'other things i wont say', icon: <Lock size={16} />, color: 'bg-black text-white', border: 'border-zinc-800' },
  { id: 'wall', label: 'Wall Stare', icon: <Eye size={16} />, color: 'bg-[#064E3B] text-[#BEF264]', border: 'border-[#BEF264]' },
  { id: 'other', label: 'Other...', icon: <Plus size={16} />, color: 'bg-transparent text-zinc-400', border: 'border-dashed border-zinc-500' },
];

const OxygenRoom: React.FC<OxygenRoomProps> = ({ onReturn }) => {
  const [activeMode, setActiveMode] = useState<string | null>(null);
  const [customAction, setCustomAction] = useState('');

  return (
    <div className="fixed inset-0 z-[150] bg-[#050505] flex flex-col items-center justify-center p-6 animate-in fade-in duration-500 overflow-hidden">
      {/* Ambient Glow - Subtle */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[80vw] h-[80vw] bg-gradient-to-tr from-[#FF6B00]/8 via-transparent to-[#3B82F6]/8 rounded-full blur-[120px]" />
      </div>

      <div className="w-full max-w-4xl flex flex-col gap-12 relative z-10 items-center">

        {/* Header Section */}
        <div className="flex items-center justify-between w-full px-6">
           <div className="flex items-center gap-5">
              <div className="h-12 w-12 rounded-2xl bg-zinc-900 border border-white/5 flex items-center justify-center text-blue-400 shadow-2xl">
                 <Wind size={24} className="animate-pulse" />
              </div>
              <div>
                 <MicroLabel text="CHAMBER INTERMISSION" color="text-zinc-500" />
                 <h2 className="text-3xl font-black text-white tracking-tighter uppercase leading-none mt-1">Oxygen Room</h2>
              </div>
           </div>

           <div className="flex items-center gap-4">
             <BrainDump />
           </div>
        </div>

        {/* Main Content Area */}
        <div className="flex flex-col items-center gap-8 w-full">
          <div className="text-center mb-4">
            <h3 className="text-xl font-light text-zinc-400 tracking-tight">
              What happened during your <span className="text-white font-bold italic">escape?</span>
            </h3>
          </div>

          <div className="flex flex-wrap justify-center gap-3.5 max-w-3xl">
            {REST_MODES.map((mode) => (
              <button
                key={mode.id}
                onClick={() => setActiveMode(mode.id)}
                className={`
                  flex items-center gap-3 px-5 py-2.5 rounded-full border transition-all duration-300 active:scale-95
                  ${activeMode === mode.id
                    ? 'translate-y-[-4px] shadow-2xl scale-110 ring-4 ring-white/10 opacity-100'
                    : 'opacity-50 hover:opacity-100 hover:translate-y-[-2px]'}
                  ${mode.color} ${mode.border}
                `}
              >
                {mode.icon}
                <span className="text-[10px] font-black uppercase tracking-[0.2em] whitespace-nowrap">{mode.label}</span>
              </button>
            ))}
          </div>

          {/* Conditional Input for "Other" */}
          {activeMode === 'other' && (
            <div className="w-full max-w-md animate-in slide-in-from-top-4 duration-500 mt-4">
              <input
                type="text"
                value={customAction}
                onChange={(e) => setCustomAction(e.target.value)}
                placeholder="What did you get up to?"
                className="w-full bg-white/5 border-2 border-dashed border-zinc-700 rounded-full px-8 py-4 text-[11px] font-black text-white uppercase tracking-[0.2em] outline-none focus:border-[#FF6B00] focus:bg-white/10 transition-all placeholder:text-zinc-600 text-center"
              />
            </div>
          )}
        </div>

        {/* Return Button Area */}
        <div className="flex flex-col items-center w-full mt-8">
          <button
            onClick={onReturn}
            className="group flex items-center gap-4 px-12 py-5 bg-white text-black rounded-full font-black text-[10px] uppercase tracking-[0.4em] hover:bg-[#FF6B00] hover:text-white transition-all shadow-2xl active:scale-95"
          >
            <ArrowLeft size={16} className="group-hover:-translate-x-1 transition-transform" />
            I&apos;m back in focus
          </button>
        </div>

      </div>
    </div>
  );
};

export default OxygenRoom;
