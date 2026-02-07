'use client';

import React from 'react';
import { X, Brain, Shield, Zap, Target, ShoppingBag, Users, Lightbulb, Briefcase } from 'lucide-react';
import MicroLabel from './ui/MicroLabel';

interface ChamberGuideProps {
  onClose: () => void;
}

const ChamberGuide: React.FC<ChamberGuideProps> = ({ onClose }) => {
  return (
    <div className="fixed inset-0 z-[200] flex items-center justify-center p-6 bg-black/60 backdrop-blur-md animate-in fade-in duration-500">
      <div className="bg-white rounded-[4rem] w-full max-w-5xl max-h-[90vh] overflow-y-auto border-4 border-black relative shadow-[0_80px_160px_rgba(0,0,0,0.5)]">
        {/* Header Section */}
        <div className="p-12 lg:p-16 border-b border-zinc-100 flex justify-between items-start">
          <div className="max-w-xl">
            <MicroLabel text="HOW TO USE THE FOCUS CHAMBER" color="text-[#FF6B00]" />
            <h2 className="text-5xl lg:text-6xl font-light tracking-tight text-zinc-900 mt-4 leading-none">
              Master your <span className="font-black italic">Focus Flow.</span>
            </h2>
          </div>
          <button
            onClick={onClose}
            className="h-16 w-16 rounded-full bg-black text-white flex items-center justify-center hover:bg-[#FF6B00] transition-all active:scale-90 shadow-xl"
          >
            <X size={32} />
          </button>
        </div>

        {/* Content Section - Bento Layout */}
        <div className="p-12 lg:p-16 flex flex-col gap-12">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-12">
            {/* The Brain Dump Zone Concept */}
            <div className="flex flex-col">
              <div className="h-14 w-14 rounded-2xl bg-black text-white flex items-center justify-center mb-8 shadow-xl">
                <Brain size={28} />
              </div>
              <h3 className="text-2xl font-black text-zinc-900 uppercase tracking-tighter mb-6">
                The Brain Dump Zone
              </h3>

              <div className="space-y-3">
                <div className="flex items-center gap-4 p-4 rounded-[2rem] bg-zinc-50 border border-zinc-100">
                  <div className="h-10 w-10 rounded-xl bg-white flex items-center justify-center text-zinc-400">
                    <ShoppingBag size={16} />
                  </div>
                  <div>
                    <p className="text-[10px] font-black text-[#FF6B00] uppercase tracking-widest">Errands</p>
                    <p className="text-xs font-bold text-zinc-800">&quot;Buy milk&quot; or &quot;Laundry detergent&quot;</p>
                  </div>
                </div>
                <div className="flex items-center gap-4 p-4 rounded-[2rem] bg-zinc-50 border border-zinc-100">
                  <div className="h-10 w-10 rounded-xl bg-white flex items-center justify-center text-zinc-400">
                    <Users size={16} />
                  </div>
                  <div>
                    <p className="text-[10px] font-black text-[#FF6B00] uppercase tracking-widest">Social</p>
                    <p className="text-xs font-bold text-zinc-800">&quot;Text Mom&quot; or &quot;Reply to John&apos;s invite&quot;</p>
                  </div>
                </div>
                <div className="flex items-center gap-4 p-4 rounded-[2rem] bg-zinc-50 border border-zinc-100">
                  <div className="h-10 w-10 rounded-xl bg-white flex items-center justify-center text-zinc-400">
                    <Lightbulb size={16} />
                  </div>
                  <div>
                    <p className="text-[10px] font-black text-[#FF6B00] uppercase tracking-widest">Genius</p>
                    <p className="text-xs font-bold text-zinc-800">&quot;App idea for pets&quot; or &quot;Blog topic&quot;</p>
                  </div>
                </div>
                <div className="flex items-center gap-4 p-4 rounded-[2rem] bg-zinc-50 border border-zinc-100">
                  <div className="h-10 w-10 rounded-xl bg-white flex items-center justify-center text-zinc-400">
                    <Briefcase size={16} />
                  </div>
                  <div>
                    <p className="text-[10px] font-black text-[#FF6B00] uppercase tracking-widest">Projects</p>
                    <p className="text-xs font-bold text-zinc-800">&quot;Refactor CSS&quot; or &quot;Plan sprint&quot;</p>
                  </div>
                </div>
              </div>
            </div>

            {/* The Shield Concept */}
            <div className="flex flex-col">
              <div className="h-14 w-14 rounded-2xl bg-[#FF6B00] text-white flex items-center justify-center mb-8 shadow-xl shadow-orange-500/20">
                <Shield size={28} />
              </div>
              <h3 className="text-2xl font-black text-zinc-900 uppercase tracking-tighter mb-4">The Shield</h3>
              <p className="text-zinc-500 leading-relaxed mb-6 font-medium">
                The interface removes all clutter to protect your attention. Only what matters is visible.
              </p>
              <ul className="space-y-4">
                <li className="flex gap-4 items-start">
                  <div className="mt-1 h-5 w-5 bg-black rounded-full flex-shrink-0 flex items-center justify-center">
                    <Zap size={10} className="text-white" />
                  </div>
                  <p className="text-sm font-bold text-zinc-800">No sidebars or menus to distract you.</p>
                </li>
                <li className="flex gap-4 items-start">
                  <div className="mt-1 h-5 w-5 bg-black rounded-full flex-shrink-0 flex items-center justify-center">
                    <Target size={10} className="text-white" />
                  </div>
                  <p className="text-sm font-bold text-zinc-800">Hyper-clear hierarchy keeps you grounded.</p>
                </li>
              </ul>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-12 pt-12 border-t border-zinc-100">
            {/* I'm Stuck Section */}
            <div className="flex flex-col">
              <div className="mb-8">
                <div className="inline-flex px-8 py-3 rounded-full bg-zinc-100 text-zinc-900 border border-zinc-200 shadow-sm">
                  <span className="text-[11px] font-black uppercase tracking-[0.2em]">I&apos;m Stuck</span>
                </div>
              </div>
              <h3 className="text-2xl font-black text-zinc-900 uppercase tracking-tighter mb-4">Overcome Blockers</h3>
              <p className="text-zinc-500 leading-relaxed font-medium">
                Feeling overwhelmed or blocked? Pressing this unlocks alternative resources, simplified steps, and
                supportive context to help you find your momentum again.
              </p>
            </div>

            {/* Break Section */}
            <div className="flex flex-col">
              <div className="mb-8">
                <div className="inline-flex px-8 py-3 rounded-full border-2 border-[#3B82F6] text-[#3B82F6] shadow-sm">
                  <span className="text-[11px] font-black uppercase tracking-[0.2em]">Take a Break</span>
                </div>
              </div>
              <h3 className="text-2xl font-black text-zinc-900 uppercase tracking-tighter mb-4">Rhythm Tracking</h3>
              <p className="text-zinc-500 leading-relaxed font-medium">
                Stepping away? Use this for any break, even a quick one. This helps Raimon recognize your natural
                energy patterns, allowing it to schedule your work for peak productivity in less time.
              </p>
            </div>
          </div>

          {/* The Vault Concept */}
          <div className="flex flex-col bg-[#0D1117] rounded-[3rem] p-10 relative overflow-hidden group">
            <div className="absolute top-0 right-0 w-64 h-64 bg-[#FF6B00]/5 rounded-full blur-3xl pointer-events-none" />
            <div className="flex items-center gap-4 mb-6">
              <MicroLabel text="PHASE 3: THE VAULT" color="text-[#FF6B00]" />
            </div>
            <h3 className="text-3xl font-black text-white uppercase tracking-tighter mb-4">Context isolation</h3>
            <p className="text-white/60 leading-relaxed font-medium max-w-2xl">
              All files and links for your task are stored in the <span className="text-white">Vault</span>. Never
              leave the app to search for a document. Leaving the chamber is a distraction risk; staying inside the
              Vault is your superpower.
            </p>

            <button
              onClick={onClose}
              className="mt-10 self-start px-10 py-4 bg-white text-black font-black text-xs uppercase tracking-[0.2em] rounded-full hover:bg-[#FF6B00] hover:text-white transition-all active:scale-95"
            >
              Enter the Chamber
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ChamberGuide;
