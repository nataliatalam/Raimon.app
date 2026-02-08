'use client';

import React, { useEffect, useMemo, useState } from 'react';
import { ArrowRight } from 'lucide-react';
import MicroLabel from './ui/MicroLabel';
import TheVault from './TheVault';
import BrainDump from './BrainDump';
import ChamberGuide from './ChamberGuide';
import OxygenRoom from './OxygenRoom';
import styles from './FocusChamber.module.css';
import type { StoredCoachMessage } from '../../lib/activeTask';

export type FocusTask = {
  title: string;
  desc: string;
  project: string;
  duration?: string;
};

export type FocusResource = {
  id: string;
  kind: 'doc' | 'sheet' | 'link' | 'notes';
  name: string;
  action?: string;
  onClick?: () => void;
};

type Props = {
  task: FocusTask;
  coach?: StoredCoachMessage | null;
  resources?: FocusResource[];
  initialNotesOpen?: boolean;
  onSend?: (text: string) => void;
  onStuck?: () => void;
  onBreak?: () => void;
  onResume?: () => void;
  onDone?: () => void;
};

export default function FocusChamber({
  task,
  coach,
  resources = [],
  initialNotesOpen = true,
  onStuck,
  onBreak,
  onResume,
  onDone,
}: Props) {
  const [isOnBreak, setIsOnBreak] = useState(false);
  const [isGuideOpen, setIsGuideOpen] = useState(false);
  const [coachVisible, setCoachVisible] = useState(false);
  const [notesOpen, setNotesOpen] = useState(initialNotesOpen);

  useEffect(() => {
    if (!coach) {
      setCoachVisible(false);
      return;
    }
    setCoachVisible(false);
    const timeout = setTimeout(() => setCoachVisible(true), 50);
    return () => clearTimeout(timeout);
  }, [coach?.title, coach?.message, coach?.next_step]);

  const hasNotes = Boolean(task.desc?.trim());

  const resourceList = useMemo(() => {
    if (!hasNotes) return resources;
    const notesResource: FocusResource = {
      id: 'notes',
      kind: 'notes',
      name: 'Notes & description',
      action: notesOpen ? 'Hide' : 'View',
      onClick: () => setNotesOpen((open) => !open),
    };
    return [notesResource, ...resources];
  }, [hasNotes, resources, notesOpen]);

  const handleBreakToggle = () => {
    if (isOnBreak) {
      setIsOnBreak(false);
      onResume?.();
    } else {
      setIsOnBreak(true);
      onBreak?.();
    }
  };

  const stuckBtnClass =
    'px-6 py-2.5 rounded-full font-bold text-[10px] tracking-[0.2em] uppercase border border-zinc-200 bg-zinc-50 text-zinc-600 hover:bg-zinc-100 transition-all active:scale-95 whitespace-nowrap text-center';
  const breakBtnClass =
    'px-6 py-2.5 rounded-full font-bold text-[10px] tracking-[0.2em] uppercase border-2 border-[#3B82F6] bg-white text-[#3B82F6] hover:bg-blue-50 transition-all active:scale-95 whitespace-nowrap text-center shadow-sm';
  const primaryBtnClass =
    'px-8 py-2.5 rounded-full font-bold text-[10px] tracking-[0.2em] uppercase bg-black text-white hover:bg-[#FF6B00] transition-all shadow-lg shadow-black/5 active:scale-95 whitespace-nowrap text-center';

  return (
    <div className={`w-full h-full flex flex-col gap-4 pt-14 pl-14 pr-8 pb-8 animate-in fade-in slide-in-from-bottom-4 duration-1000 relative ${isOnBreak ? styles.breakMode : ''}`}>
      {/* Oxygen Room Overlay */}
      {isOnBreak && <OxygenRoom onReturn={handleBreakToggle} />}

      {/* Workspace Header with Integrated Brain Dump */}
      <div className={`flex items-end justify-between shrink-0 ${isOnBreak ? 'opacity-0 pointer-events-none' : ''}`}>
        <div className="flex items-center gap-8">
          <div>
            <MicroLabel text="RAIMON WORKSPACE" color="text-zinc-400" />
            <div className="flex items-center gap-6 mt-1">
              <h2 className="text-4xl font-medium tracking-tight text-zinc-900">
                Focus <span className="text-[#FF6B00] font-black italic">Chamber</span>
              </h2>
              <BrainDump />
            </div>
          </div>
        </div>

        <div className="flex items-center gap-4 pb-1">
          {/* Guide Button */}
          <button
            onClick={() => setIsGuideOpen(true)}
            className="flex items-center gap-3 px-4 py-2 bg-[#0D1117] rounded-full border border-white/10 hover:border-[#FF6B00]/40 transition-all hover:shadow-xl hover:shadow-black/20 group"
          >
            <span className="text-[11px] font-black text-[#FF6B00] uppercase tracking-wider">Guide</span>
            <div className="h-4 w-[1px] bg-white/10 group-hover:bg-[#FF6B00]/30" />
            <div className="flex items-center gap-1.5">
              <span className="text-[9px] font-black tracking-[0.15em] text-white/40 group-hover:text-white uppercase transition-colors">
                Open
              </span>
              <ArrowRight
                size={10}
                className="text-white/20 group-hover:text-white transition-transform group-hover:translate-x-0.5"
              />
            </div>
          </button>

          <div className="flex items-center gap-3">
            <button className={stuckBtnClass} onClick={onStuck}>
              I&apos;m Stuck
            </button>
            <button
              className={breakBtnClass}
              onClick={handleBreakToggle}
            >
              Break
            </button>
            <button className={primaryBtnClass} onClick={onDone}>
              Mark as Done
            </button>
          </div>
        </div>
      </div>

      {/* Modern Bento Layout */}
      <div className={`flex-1 grid grid-cols-12 gap-4 min-h-0 pb-2 ${isOnBreak ? 'opacity-0 pointer-events-none' : ''}`}>
        {/* Task Focus Card */}
        <div className="col-span-7 flex flex-col bg-white rounded-[2.5rem] shadow-[0_20px_60px_rgba(0,0,0,0.02)] border border-zinc-100 overflow-hidden relative group hover:shadow-[0_30px_80px_rgba(0,0,0,0.04)] transition-all duration-700">
          <div className="p-6 lg:p-8 flex flex-col h-full overflow-y-auto">
            <div className="flex items-center gap-4 mb-6">
              <div className="px-3 py-1 bg-[#FF6B00]/5 rounded-full border border-[#FF6B00]/10">
                <span className="font-black text-[9px] tracking-widest text-[#FF6B00] uppercase">{task.project}</span>
              </div>
            </div>

            <div className="mb-6">
              <h1 className="text-3xl lg:text-5xl font-light tracking-tight leading-tight text-zinc-900 whitespace-pre-line">
                {task.title}
                <span className="text-[#FF6B00] font-medium">.</span>
              </h1>
            </div>

            {coach && (
              <div
                className={`mt-4 pt-4 border-t border-zinc-200 transition-all duration-500 ease-out ${
                  coachVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-2'
                }`}
                style={{ transitionDelay: coachVisible ? '0.5s' : '0s' }}
              >
                <div className="space-y-1.5">
                  <p className="text-base font-semibold text-zinc-900">{coach.title}</p>
                  <p className="text-[13px] text-zinc-500 leading-relaxed">{coach.message}</p>
                  {coach.next_step ? (
                    <p className="text-xs font-semibold text-[#FF6B00] tracking-wide">
                      <span className="mr-1">→</span>
                      {coach.next_step}
                    </p>
                  ) : null}
                </div>
              </div>
            )}

            <div className="flex-1 w-full max-w-2xl">
              <div
                className="overflow-hidden transition-all duration-[350ms] ease-[cubic-bezier(0.4,0,0.2,1)]"
                style={{
                  maxHeight: notesOpen && hasNotes ? '500px' : '0px',
                  opacity: notesOpen && hasNotes ? 1 : 0,
                }}
              >
                <div className="pt-4 mt-4 border-t border-zinc-200">
                  <div className="mb-2">
                    <MicroLabel text="OBJECTIVE & CONTEXT" />
                  </div>
                  <p className="text-base lg:text-xl font-normal text-zinc-400 leading-relaxed tracking-tight whitespace-pre-line">
                    {task.desc}
                  </p>
                </div>
              </div>
            </div>
          </div>

          <div className="absolute -bottom-24 -right-24 w-64 h-64 bg-[#FF6B00]/5 rounded-full blur-3xl opacity-50 pointer-events-none" />
        </div>

        {/* Sidebar - The Vault */}
        <div className="col-span-5 flex flex-col overflow-hidden">
          <div className="flex-1 bg-[#0D1117] rounded-[2.5rem] shadow-2xl border border-white/5 flex flex-col overflow-hidden hover:shadow-[0_40px_100px_rgba(0,0,0,0.3)] transition-all duration-700">
            <TheVault resources={resourceList} />
          </div>
        </div>
      </div>

      {/* Chamber Guide Overlay */}
      {isGuideOpen && <ChamberGuide onClose={() => setIsGuideOpen(false)} />}
    </div>
  );
}
