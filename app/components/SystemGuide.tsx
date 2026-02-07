'use client';

import React from 'react';
import MicroLabel from './ui/MicroLabel';
import {
  Home,
  Target,
  Shield,
  PlusSquare,
  FolderOpen,
  Calendar as CalendarIcon,
  Zap,
  X,
  Brain,
  ArrowRight,
  HelpCircle,
} from 'lucide-react';

interface SystemGuideProps {
  onClose: () => void;
}

const features = [
  {
    title: 'Check-in',
    desc: 'The ritual of grounding. We use this to acknowledge your mental state before work starts.',
    icon: <Zap size={20} />,
    color: 'text-[#FF6B00]',
  },
  {
    title: 'Dashboard Home',
    desc: "Your command center. View your 'Start Do' streak, next meeting, and the one task that matters.",
    icon: <Home size={20} />,
    color: 'text-zinc-900',
  },
  {
    title: 'Task Page',
    desc: 'Deep dive into objectives. Where you see your notes, time estimates, and sub-goals.',
    icon: <Target size={20} />,
    color: 'text-zinc-900',
  },
  {
    title: 'Focus Chamber',
    desc: 'The deep-work zone. Complete immersion where your tasks and logged resources live in perfect harmony.',
    icon: <Shield size={20} />,
    color: 'text-[#FF6B00]',
  },
  {
    title: 'Add Project',
    desc: 'Creation zone when youre ready to build something great.',
    icon: <PlusSquare size={20} />,
    color: 'text-zinc-900',
  },
  {
    title: 'My Projects',
    desc: 'The vault of all your projects—active, paused, some in the beyond and others in the grave.',
    icon: <FolderOpen size={20} />,
    color: 'text-zinc-900',
  },
  {
    title: 'Project Filter',
    desc: "The 'All Projects' toggle. Choose whether you're seeing tasks from your entire universe, or just specific work and personal buckets.",
    visual: (
      <div className="bg-white border border-zinc-200 rounded-full px-6 py-3 flex items-center gap-4 shadow-sm group-hover:border-[#FF6B00] transition-colors">
        <span className="text-[10px] font-black text-zinc-900 uppercase tracking-widest">All Projects</span>
        <div className="h-4 w-[1px] bg-zinc-200" />
        <div className="flex items-center gap-2 text-[#FF6B00]">
          <span className="text-[9px] font-black uppercase tracking-widest">Edit</span>
          <ArrowRight size={12} />
        </div>
      </div>
    ),
  },
  {
    title: 'Brain Dump',
    desc: 'Your cognitive safety net. Clear your mind instantly by offloading thoughts, files, and links to be processed by Raimon later.',
    visual: (
      <div className="bg-white border border-zinc-100 rounded-full p-1.5 pr-8 flex items-center gap-3 shadow-sm group-hover:border-[#FF6B00] transition-all origin-left">
        <div className="w-10 h-10 bg-black rounded-full flex items-center justify-center text-white shrink-0 group-hover:scale-105 transition-transform">
          <Brain size={16} />
        </div>
        <div className="flex flex-col items-start leading-none">
          <span className="text-[9px] font-black uppercase tracking-tight text-black">Brain Dump</span>
          <span className="text-[7px] font-bold text-zinc-400 uppercase tracking-widest mt-1">Park your thoughts</span>
        </div>
      </div>
    ),
  },
  {
    title: 'Calendar',
    desc: "It's just a calendar.",
    icon: <CalendarIcon size={20} />,
    color: 'text-zinc-900',
  },
];

const SystemGuide: React.FC<SystemGuideProps> = ({ onClose }) => {
  return (
    <div className="fixed inset-0 z-[250] flex items-center justify-center p-6 bg-black/60 backdrop-blur-xl animate-in fade-in duration-300">
      <div className="bg-white rounded-[4rem] w-full max-w-6xl max-h-[90vh] overflow-y-auto custom-scrollbar border-4 border-black relative shadow-2xl flex flex-col">
        <div className="pt-12 px-12 lg:pt-16 lg:px-16 pb-8 flex justify-between items-start z-20">
          <div className="max-w-xl">
            <MicroLabel text="SYSTEM BLUEPRINT" color="text-[#FF6B00]" />
            <h2 className="text-4xl lg:text-5xl font-black text-black tracking-tighter uppercase leading-none mt-4">
              Understanding Raimon
            </h2>
            <p className="text-lg text-zinc-400 font-medium mt-4">
              Everything in this ecosystem is built to lower your cognitive load. Here is how we protect your focus.
            </p>
          </div>
          <button
            onClick={onClose}
            className="h-14 w-14 rounded-full bg-black text-white flex items-center justify-center hover:bg-[#FF6B00] transition-all active:scale-90 shadow-xl"
            aria-label="Close guide"
          >
            <X size={28} />
          </button>
        </div>

        <div className="px-12 lg:px-16 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 pb-12">
          {features.map((f, i) => (
            <div
              key={i}
              className="group p-8 bg-zinc-50 border border-zinc-100 rounded-[2.5rem] hover:bg-white hover:shadow-xl hover:border-[#FF6B00]/20 transition-all duration-500 flex flex-col items-start"
            >
              <div className="mb-6 h-12 flex items-center">
                {f.visual ? (
                  f.visual
                ) : (
                  <div className={`h-12 w-12 rounded-2xl bg-white ${f.color} flex items-center justify-center group-hover:scale-110 transition-transform shadow-sm`}>
                    {f.icon}
                  </div>
                )}
              </div>
              <h3 className="text-lg font-black text-black uppercase tracking-tight mb-3">{f.title}</h3>
              <p className="text-sm text-zinc-500 font-medium leading-relaxed">{f.desc}</p>
            </div>
          ))}

          <div className="p-8 bg-black border border-black rounded-[2.5rem] shadow-xl flex flex-col justify-between group overflow-hidden relative min-h-[220px]">
            <div className="relative z-10">
              <div className="mb-6">
                <div className="bg-white rounded-full p-2 pr-10 flex items-center gap-4 w-fit shadow-sm">
                  <div className="w-10 h-10 bg-black rounded-full flex items-center justify-center text-white shrink-0">
                    <HelpCircle size={24} />
                  </div>
                  <span className="text-[11px] font-black uppercase tracking-tight text-black whitespace-nowrap">How it works</span>
                </div>
              </div>
              <h3 className="text-lg font-black text-white uppercase tracking-tight mb-3">Need more?</h3>
              <p className="text-sm text-white/50 font-medium leading-relaxed">
                For deeper insights into any specific feature, look for the question pill within that view.
              </p>
            </div>
            <div className="absolute top-0 right-0 w-32 h-32 bg-[#FF6B00] rounded-full blur-[60px] opacity-10" />
          </div>
        </div>

        <div className="p-12 lg:p-16 flex justify-center">
          <button
            onClick={onClose}
            className="px-12 py-5 bg-black text-white rounded-full font-black text-xs uppercase tracking-[0.4em] hover:bg-[#FF6B00] transition-all shadow-xl active:scale-95"
          >
            Got it, let&apos;s work
          </button>
        </div>
      </div>
    </div>
  );
};

export default SystemGuide;
