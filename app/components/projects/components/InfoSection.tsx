'use client';

import React, { useState } from 'react';
import {
  X, Eye, Pause, Skull, Trash2,
  ArrowRight, ChevronDown
} from 'lucide-react';

export default function InfoSection() {
  const [isOpen, setIsOpen] = useState(false);
  const [activeTab, setActiveTab] = useState<'sections' | 'buttons'>('sections');

  // For Sections (Accordion style)
  const [expandedSection, setExpandedSection] = useState<string | null>(null);

  // For Buttons (Selection style)
  const [selectedButton, setSelectedButton] = useState<string | null>(null);

  const toggleSection = (id: string) => {
    setExpandedSection(expandedSection === id ? null : id);
  };

  const sectionsData = [
    { id: 'active', title: 'Active', desc: 'Current projects. Raimon actively generates tasks for these to keep you moving forward.' },
    { id: 'paused', title: 'Paused', desc: 'Work in progress on hold. It stays here safely, Raimon just wont show tasks for that project until you unpause.' },
    { id: 'beyond', title: 'Beyond', desc: 'Projects that were once just a thought, became a memory. A celebration of reality, now accomplished.' },
    { id: 'graveyard', title: 'Graveyard', desc: 'Erased but not gone. Give flowers to remember them, or resurrect if you change your mind.' },
  ];

  const buttonsData = [
    { id: 'view', title: 'View', icon: <Eye size={20} />, desc: 'Open project details and see current tasks.' },
    { id: 'pause', title: 'Pause', icon: <Pause size={20} />, desc: 'Stop task generation temporarily until unpaused.' },
    { id: 'bury', title: 'Bury', icon: <Skull size={20} />, desc: 'Move project to the Graveyard.' },
    { id: 'erase', title: 'Erase', icon: <Trash2 size={20} />, desc: 'Permanently delete. No return.' },
  ];

  if (!isOpen) {
    // Collapsed View matches calendar pill styling for consistency
    return (
      <button
        type="button"
        onClick={() => setIsOpen(true)}
        className="h-14 px-6 rounded-full bg-white text-black flex items-center gap-3 hover:bg-orange-500 hover:text-white transition-all active:scale-95 group border border-gray-100 shadow-sm min-w-[220px]"
      >
        <div className="w-5 h-5 bg-black group-hover:bg-white rounded-full flex items-center justify-center transition-colors">
          <span className="text-[9px] font-black text-white group-hover:text-black">?</span>
        </div>
        <div className="flex flex-col items-start leading-tight">
          <span className="text-[10px] font-black uppercase tracking-[0.2em]">Guide</span>
          <span className="text-xs font-medium tracking-tight">How it works</span>
        </div>
      </button>
    );
  }

  // Expanded View
  return (
    <div className="animate-in fade-in zoom-in-95 duration-200">
      <div className="bg-[#0f172a] w-full max-w-85 rounded-[20px] p-5 shadow-xl shadow-slate-300/40 border border-slate-800 relative overflow-hidden">
         {/* Decorative faint glow */}
         <div className="absolute top-0 right-0 w-40 h-40 bg-orange-500/5 rounded-full blur-3xl -translate-y-1/2 translate-x-1/2 pointer-events-none"></div>

         {/* Header & Close */}
         <div className="flex justify-between items-start mb-5 relative z-10">
            <div>
                <h2 className="text-3xl font-bold text-orange-500 tracking-tighter mb-1 leading-none">Guide</h2>
                <p className="text-white/80 text-sm font-medium tracking-tight">How it works</p>
            </div>
            <button
              onClick={() => setIsOpen(false)}
              className="p-2 rounded-full bg-white/10 text-white/70 hover:bg-white/20 hover:text-white transition-colors"
            >
              <X size={18} />
            </button>
         </div>

         {/* Pill Toggle */}
         <div className="bg-slate-800/50 p-1 rounded-full flex mb-5 relative z-10 border border-slate-700/50">
            <button
               onClick={() => { setActiveTab('sections'); setExpandedSection(null); setSelectedButton(null); }}
               className={`flex-1 py-2 rounded-full text-sm font-light tracking-wide transition-all duration-300 ${
                 activeTab === 'sections' ? 'bg-white text-slate-900 shadow-md' : 'text-slate-400 hover:text-slate-200'
               }`}
            >
               Sections
            </button>
            <button
               onClick={() => { setActiveTab('buttons'); setExpandedSection(null); setSelectedButton(null); }}
               className={`flex-1 py-2 rounded-full text-sm font-light tracking-wide transition-all duration-300 ${
                 activeTab === 'buttons' ? 'bg-white text-slate-900 shadow-md' : 'text-slate-400 hover:text-slate-200'
               }`}
            >
               Buttons
            </button>
         </div>

         {/* Content Area */}
         <div className="relative z-10 min-h-50">
            {activeTab === 'sections' ? (
                <div className="space-y-3">
                    {sectionsData.map((item) => {
                        const isExpanded = expandedSection === item.id;
                        return (
                            <div key={item.id} className="border-b border-slate-800/50 pb-3 last:border-0">
                                <button
                                    onClick={() => toggleSection(item.id)}
                                    className="w-full flex items-center justify-between text-left group"
                                >
                                    <span className={`text-lg font-light tracking-tight transition-colors duration-300 ${isExpanded ? 'text-orange-400' : 'text-white group-hover:text-white/80'}`}>
                                        {item.title}
                                    </span>
                                    <ChevronDown
                                        size={18}
                                        className={`text-slate-500 transition-transform duration-300 ${isExpanded ? 'rotate-180 text-orange-400' : ''}`}
                                    />
                                </button>
                                <div className={`grid transition-all duration-300 ease-in-out ${isExpanded ? 'grid-rows-[1fr] opacity-100 mt-2' : 'grid-rows-[0fr] opacity-0'}`}>
                                    <div className="overflow-hidden">
                                        <p className="text-sm text-slate-300 font-light leading-relaxed">
                                            {item.desc}
                                        </p>
                                    </div>
                                </div>
                            </div>
                        );
                    })}
                </div>
            ) : (
                <div className="animate-in fade-in slide-in-from-bottom-4 duration-500">
                    <div className="grid grid-cols-4 gap-2 mb-5">
                        {buttonsData.map((btn) => (
                            <button
                                key={btn.id}
                                onClick={() => setSelectedButton(btn.id)}
                                className={`
                                    aspect-square rounded-xl flex flex-col items-center justify-center gap-1 transition-all duration-300
                                    ${selectedButton === btn.id
                                        ? 'bg-orange-500 text-white shadow-lg shadow-orange-500/20 scale-105'
                                        : 'bg-slate-800 text-slate-400 hover:bg-slate-700 hover:text-slate-200'
                                    }
                                `}
                            >
                                {btn.icon}
                            </button>
                        ))}
                    </div>

                    <div className="bg-slate-800/50 rounded-2xl p-4 min-h-25 flex items-center justify-center border border-slate-700/50">
                        {selectedButton ? (
                            <p className="text-sm text-center text-slate-200 font-light leading-relaxed animate-in fade-in zoom-in-95 duration-200">
                                {buttonsData.find(b => b.id === selectedButton)?.desc}
                            </p>
                        ) : (
                            <p className="text-slate-500 text-sm font-light italic text-center">
                                Tap a button above to see what it does.
                            </p>
                        )}
                    </div>
                </div>
            )}
         </div>

      </div>
    </div>
  );
}
