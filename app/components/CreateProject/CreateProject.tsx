'use client';

import React, { useEffect, useMemo, useRef, useState } from 'react';
import { apiFetch, ApiError } from '../../../lib/api-client';
import type { ApiSuccessResponse, ProjectApiRecord } from '../../../types/api';

/**
 * HowItWorksPill Component
 *
 * Triggers a "System Blueprint" style modal that explains the Raimon ecosystem.
 * Matches the requested aesthetic: high-contrast headers, grid-based info cards, and clean UI.
 */
const HowItWorksPill: React.FC = () => {
  const [isOpen, setIsOpen] = useState(false);

  // Prevent scrolling when modal is open
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = 'unset';
    }
    return () => {
      document.body.style.overflow = 'unset';
    };
  }, [isOpen]);

  // Handle ESC key to close
  useEffect(() => {
    const handleEsc = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setIsOpen(false);
    };
    window.addEventListener('keydown', handleEsc);
    return () => window.removeEventListener('keydown', handleEsc);
  }, []);

  return (
    <>
      {/* The Trigger Pill */}
      <button
        type="button"
        onClick={() => setIsOpen(true)}
        className="h-10 px-6 rounded-full bg-white text-black flex items-center gap-2 hover:bg-orange-500 hover:text-white transition-all active:scale-95 group border border-gray-100 shadow-sm"
      >
        <div className="w-4 h-4 bg-black group-hover:bg-white rounded-full flex items-center justify-center transition-colors">
          <span className="text-[8px] font-black text-white group-hover:text-black">?</span>
        </div>
        <span className="text-[9px] font-black uppercase tracking-[0.1em]">How it works</span>
      </button>

      {/* The System Blueprint Modal */}
      {isOpen && (
        <div className="fixed inset-0 z-[100] flex items-center justify-center p-6 md:p-12 animate-in fade-in duration-300">
          {/* Backdrop */}
          <div
            className="absolute inset-0 bg-black/60 backdrop-blur-sm"
            onClick={() => setIsOpen(false)}
          />

          {/* Modal Container */}
          <div className="relative w-full max-w-6xl bg-white rounded-[60px] shadow-2xl overflow-hidden flex flex-col max-h-[90vh] animate-in zoom-in-95 slide-in-from-bottom-10 duration-500">
            {/* Close Button */}
            <button
              type="button"
              onClick={() => setIsOpen(false)}
              className="absolute top-10 right-10 w-12 h-12 bg-black text-white rounded-full flex items-center justify-center hover:scale-110 transition-transform z-10 shadow-lg"
            >
              <svg
                width="20"
                height="20"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2.5"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                <line x1="18" y1="6" x2="6" y2="18"></line>
                <line x1="6" y1="6" x2="18" y2="18"></line>
              </svg>
            </button>

            {/* Scrollable Content */}
            <div className="flex-1 overflow-y-auto p-12 md:p-20 custom-scrollbar">
              <header className="mb-16">
                <span className="text-orange-500 font-bold text-xs tracking-[0.2em] uppercase mb-4 block">System Blueprint</span>
                <h1 className="text-6xl font-black text-zinc-900 leading-[1.1] tracking-tighter">
                  UNDERSTANDING<br />THE FLOW
                </h1>
                <p className="text-zinc-400 text-xl mt-6 font-medium max-w-2xl leading-relaxed">
                  Everything in this ecosystem is built to lower your cognitive load. Here is how we protect your focus.
                </p>
              </header>

              {/* Blueprint Grid */}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {/* 1. Workspace */}
                <div className="bg-zinc-50 rounded-[40px] p-10 flex flex-col gap-6 hover:bg-zinc-100/80 transition-colors">
                  <div className="w-12 h-12 rounded-2xl bg-white shadow-sm flex items-center justify-center text-orange-500">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
                      <line x1="3" y1="9" x2="21" y2="9"></line>
                      <line x1="9" y1="21" x2="9" y2="9"></line>
                    </svg>
                  </div>
                  <div>
                    <h3 className="text-zinc-900 font-black text-xl mb-3 tracking-tight">WORKSPACE</h3>
                    <p className="text-zinc-500 text-[15px] leading-relaxed">
                      "Choose your workspace" creates a mental boundary. <span className="text-zinc-900 font-bold">Work</span> vs <span className="text-zinc-900 font-bold">Personal</span> buckets ensure your universe stays organized and relevant.
                    </p>
                  </div>
                </div>

                {/* 2. Timelines */}
                <div className="bg-zinc-50 rounded-[40px] p-10 flex flex-col gap-6 hover:bg-zinc-100/80 transition-colors">
                  <div className="w-12 h-12 rounded-2xl bg-white shadow-sm flex items-center justify-center text-orange-500">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <circle cx="12" cy="12" r="10"></circle>
                      <polyline points="12 6 12 12 16 14"></polyline>
                    </svg>
                  </div>
                  <div>
                    <h3 className="text-zinc-900 font-black text-xl mb-3 tracking-tight">TIMELINES</h3>
                    <p className="text-zinc-500 text-[15px] leading-relaxed">
                      Time is flexible. Set dates for a <span className="text-zinc-900 font-bold italic">whole project</span> or specific <span className="text-zinc-900 font-bold italic">tasks</span>. Timelines and notes are always optional—only add what helps.
                    </p>
                  </div>
                </div>

                {/* 3. The Why */}
                <div className="bg-zinc-50 rounded-[40px] p-10 flex flex-col gap-6 hover:bg-zinc-100/80 transition-colors">
                  <div className="w-12 h-12 rounded-2xl bg-white shadow-sm flex items-center justify-center text-orange-500">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="M12 2L2 7l10 5 10-5-10-5z"></path>
                      <path d="M2 17l10 5 10-5"></path>
                      <path d="M2 12l10 5 10-5"></path>
                    </svg>
                  </div>
                  <div>
                    <h3 className="text-zinc-900 font-black text-xl mb-3 tracking-tight">THE "WHY"</h3>
                    <p className="text-zinc-500 text-[15px] leading-relaxed">
                      This is the grounding ritual. When Raimon understands your vision, it can <span className="text-zinc-900 font-bold">proactively assist</span> and protect your focus at every step.
                    </p>
                  </div>
                </div>

                {/* 4. Team Execution */}
                <div className="bg-zinc-50 rounded-[40px] p-10 flex flex-col gap-6 hover:bg-zinc-100/80 transition-colors border-2 border-transparent hover:border-orange-100">
                  <div className="w-12 h-12 rounded-2xl bg-white shadow-sm flex items-center justify-center text-orange-500">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path>
                      <circle cx="9" cy="7" r="4"></circle>
                      <path d="M23 21v-2a4 4 0 0 0-3-3.87"></path>
                      <path d="M16 3.13a4 4 0 0 1 0 7.75"></path>
                    </svg>
                  </div>
                  <div>
                    <h3 className="text-zinc-900 font-black text-xl mb-3 tracking-tight">WHO'S INVOLVED</h3>
                    <p className="text-zinc-500 text-[15px] leading-relaxed">
                      Knowing who is involved and their roles helps Raimon build an <span className="text-zinc-900 font-bold italic">execution blueprint</span> that works for everyone, not just you.
                    </p>
                  </div>
                </div>

                {/* 5. Resource Hub */}
                <div className="bg-zinc-50 rounded-[40px] p-10 flex flex-col gap-6 hover:bg-zinc-100/80 transition-colors">
                  <div className="w-12 h-12 rounded-2xl bg-white shadow-sm flex items-center justify-center text-orange-500">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="M15 7h3a5 5 0 0 1 5 5 5 5 0 0 1-5 5h-3m-6 0H6a5 5 0 0 1-5-5 5 5 0 0 1 5-5h3"></path>
                      <line x1="8" y1="12" x2="16" y2="12"></line>
                    </svg>
                  </div>
                  <div>
                    <h3 className="text-zinc-900 font-black text-xl mb-3 tracking-tight">RESOURCE HUB</h3>
                    <p className="text-zinc-500 text-[15px] leading-relaxed">
                      Upload files and links directly to the project. Access them <span className="text-zinc-900 font-bold">instantly</span> while doing tasks—no more hunting through 20 open tabs.
                    </p>
                  </div>
                </div>

                {/* 6. Vault Management */}
                <div className="bg-zinc-50 rounded-[40px] p-10 flex flex-col gap-6 hover:bg-zinc-100/80 transition-colors">
                  <div className="w-12 h-12 rounded-2xl bg-white shadow-sm flex items-center justify-center text-orange-500">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"></path>
                    </svg>
                  </div>
                  <div>
                    <h3 className="text-zinc-900 font-black text-xl mb-3 tracking-tight">PROJECT VAULT</h3>
                    <p className="text-zinc-500 text-[15px] leading-relaxed">
                      Once created, your work lives in <span className="text-zinc-900 font-bold italic">My Projects</span>. Active, paused, or archived—you can <span className="text-zinc-900 font-bold underline decoration-orange-200 underline-offset-4">edit or erase</span> anything at any time.
                    </p>
                  </div>
                </div>
              </div>

              <footer className="mt-20 pt-12 border-t border-zinc-100 flex justify-between items-center">
                <div className="flex gap-4">
                  <div className="w-2 h-2 rounded-full bg-orange-500 animate-pulse"></div>
                  <div className="w-2 h-2 rounded-full bg-zinc-200"></div>
                  <div className="w-2 h-2 rounded-full bg-zinc-200"></div>
                </div>
                <button
                  type="button"
                  onClick={() => setIsOpen(false)}
                  className="px-10 py-5 bg-zinc-900 text-white rounded-3xl font-bold tracking-widest uppercase hover:scale-105 active:scale-95 transition-all shadow-xl"
                >
                  Got the blueprint
                </button>
              </footer>
            </div>
          </div>
        </div>
      )}

      <style>{`
        .custom-scrollbar::-webkit-scrollbar {
          width: 6px;
        }
        .custom-scrollbar::-webkit-scrollbar-track {
          background: transparent;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb {
          background: #f1f1f1;
          border-radius: 20px;
          border: 4px solid white;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb:hover {
          background: #e4e4e7;
        }
      `}</style>
    </>
  );
};

type Props = {
  onCreated?: (projectId: string) => void;
};

type Person = {
  name: string;
  note: string;
};

type TaskItem = {
  title: string;
  note: string;
  deadlineDate?: string;
  deadlineTime?: string;
  showNote?: boolean;
};

const WORK_COLORS = ['#F97316', '#8B5CF6', '#3B82F6', '#EC4899'];
const PERSONAL_COLORS = ['#10B981', '#F59E0B', '#60A5FA', '#A855F7'];

function pickColor(type: 'work' | 'personal') {
  const arr = type === 'work' ? WORK_COLORS : PERSONAL_COLORS;
  return arr[Math.floor(Math.random() * arr.length)];
}

function combineDateTime(date?: string, time?: string) {
  if (!date) return undefined;
  const safeTime = time && time.length > 0 ? time : '23:59';
  return `${date}T${safeTime}:00`;
}

export default function CreateProject({ onCreated }: Props) {
  // -- State --
  const [name, setName] = useState('');
  const [type, setType] = useState<'work' | 'personal'>('work');
  const [brief, setBrief] = useState('');

  // Tasks state updated to handle objects and visibility
  const [tasks, setTasks] = useState<TaskItem[]>([{ title: '', note: '', showNote: false, deadlineDate: '', deadlineTime: '' }]);

  const [timeline, setTimeline] = useState<'Today' | 'Week' | 'Month' | 'Long-term'>('Week');
  const [deadlineMonth, setDeadlineMonth] = useState('');
  const [deadlineDay, setDeadlineDay] = useState('');
  const [deadlineYear, setDeadlineYear] = useState('');
  const [deadlineTime, setDeadlineTime] = useState('');

  const [why, setWhy] = useState<string[]>([]);
  const [people, setPeople] = useState<'me' | 'others'>('me');

  // People list state
  const [othersList, setOthersList] = useState<Person[]>([]);
  const [otherName, setOtherName] = useState('');
  const [otherNote, setOtherNote] = useState('');

  const [files, setFiles] = useState<File[]>([]);
  const [links, setLinks] = useState<string[]>([]);
  const [linkInput, setLinkInput] = useState('');

  const [serverError, setServerError] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isDragging, setIsDragging] = useState(false);

  const nameInputRef = useRef<HTMLInputElement | null>(null);
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  const canCreate = name.trim().length > 0 && !isSubmitting;

  const yearOptions = useMemo(() => {
    const currentYear = new Date().getFullYear();
    return Array.from({ length: 7 }, (_, i) => String(currentYear + i));
  }, []);

  // -- Helpers --
  function addTaskRow() {
    setTasks((prev) => [...prev, { title: '', note: '', showNote: false, deadlineDate: '', deadlineTime: '' }]);
  }

  function updateTask(index: number, field: keyof TaskItem, value: string | boolean) {
    setTasks(prev => prev.map((item, i) => i === index ? { ...item, [field]: value } : item));
  }

  function toggleWhy(label: string) {
    setWhy((prev) => (prev.includes(label) ? prev.filter((x) => x !== label) : [...prev, label]));
  }

  function addFiles(list: FileList | null) {
    if (!list) return;
    setFiles((prev) => [...prev, ...Array.from(list)]);
  }

  function removeFile(indexToRemove: number) {
    setFiles((prev) => prev.filter((_, index) => index !== indexToRemove));
  }

  function handleDragOver(e: React.DragEvent) {
    e.preventDefault();
    setIsDragging(true);
  }

  function handleDragLeave(e: React.DragEvent) {
    e.preventDefault();
    setIsDragging(false);
  }

  function handleDrop(e: React.DragEvent) {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      addFiles(e.dataTransfer.files);
    }
  }

  function handleAddLink() {
    if (!linkInput.trim()) return;
    setLinks(prev => [...prev, linkInput.trim()]);
    setLinkInput('');
  }

  function removeLink(indexToRemove: number) {
    setLinks(prev => prev.filter((_, index) => index !== indexToRemove));
  }

  function handleAddPerson() {
    if (!otherName.trim()) return;
    setOthersList(prev => [...prev, { name: otherName.trim(), note: otherNote.trim() }]);
    setOtherName('');
    setOtherNote('');
  }

  function removePerson(indexToRemove: number) {
    setOthersList(prev => prev.filter((_, index) => index !== indexToRemove));
  }

  const deadlineDateOnly = useMemo(() => {
    if (!deadlineMonth || !deadlineDay || !deadlineYear) return undefined;
    return `${deadlineYear}-${deadlineMonth}-${deadlineDay}`;
  }, [deadlineMonth, deadlineDay, deadlineYear]);

  const deadlineIso = useMemo(() => {
    if (!deadlineDateOnly) return undefined;
    return combineDateTime(deadlineDateOnly, deadlineTime);
  }, [deadlineDateOnly, deadlineTime]);

  async function handleCreate() {
    if (!canCreate) return;
    setServerError('');
    setIsSubmitting(true);
    try {
      // Filter out tasks with empty titles and clean inputs
      const cleanTasks = tasks
        .filter(t => t.title.trim().length > 0)
        .map(t => ({
          title: t.title.trim(),
          note: t.note.trim() || undefined,
          deadline: combineDateTime(t.deadlineDate, t.deadlineTime),
        }));

      const payload: Record<string, unknown> = {
        name: name.trim(),
        description: brief.trim() || undefined,
        priority: type === 'work' ? 2 : 1,
        color: pickColor(type),
        icon: type,
        details: {
          tasks: cleanTasks,
          timeline,
          why,
          people,
          others: people === 'others' ? othersList : [],
          links,
        },
      };

      if (deadlineDateOnly) {
        payload.target_end_date = deadlineDateOnly;
      }

      if (deadlineIso) {
        (payload.details as Record<string, unknown>).deadline = deadlineIso;
      }

      const response = await apiFetch<ApiSuccessResponse<{ project: ProjectApiRecord }>>('/api/projects', {
        method: 'POST',
        body: payload,
      });

      const projectId = response.data.project.id;

      if (files.length) {
        const uploadData = new FormData();
        files.forEach((file) => {
          uploadData.append('files', file, file.name);
        });

        try {
          await apiFetch(`/api/projects/${projectId}/files`, {
            method: 'POST',
            body: uploadData,
          });
        } catch (uploadError) {
          console.error('Failed to upload project files', uploadError);
          setServerError('Project created, but some files could not be uploaded.');
        }
      }

      onCreated?.(projectId);
    } catch (err) {
      if (err instanceof ApiError) {
        setServerError(err.message);
      } else {
        setServerError('Failed to create project. Please try again.');
      }
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div className="w-full max-w-5xl mx-auto">

      {/* Hero */}
      <div className="flex flex-col md:flex-row md:items-start md:justify-between gap-6 mb-12">
        <div className="text-center md:text-left flex-1">
          <h1 className="text-[52px] font-light text-[#1A1A1A] tracking-[-0.03em] leading-[1.1] mb-2">
            Let&apos;s build <span className="bg-linear-to-br from-[#A7F3D0] via-[#93C5FD] to-[#C4B5FD] bg-clip-text text-transparent">something great.</span>
          </h1>
        </div>
        <div className="flex justify-center md:justify-end">
          <HowItWorksPill />
        </div>
      </div>

      {serverError && (
        <div className="mb-8 p-4 rounded-2xl bg-red-50 border border-red-100 text-red-600 font-medium text-center">
          {serverError}
        </div>
      )}

      {/* Section 1: The Basics */}
      <div className="flex items-center gap-3 mb-7 mt-8">
        <div className="w-7 h-7 rounded-full bg-[#1A1A1A] text-white text-[13px] font-bold flex items-center justify-center">1</div>
        <span className="text-[13px] font-semibold text-[#6B6B6B] uppercase tracking-widest">The Basics</span>
      </div>

      <div className="flex flex-col md:flex-row md:items-center gap-4 mb-6">
        <span className="text-2xl font-light text-[#1A1A1A] whitespace-nowrap">I&apos;m working on</span>
        <div className={`flex-1 px-5 py-3.5 bg-[#F5F3ED] border-2 border-transparent rounded-2xl transition-all focus-within:bg-white focus-within:border-[#1A1A1A] ${!canCreate && name.length > 0 ? 'border-orange-500' : ''}`}>
          <input
            ref={nameInputRef}
            value={name}
            onChange={(e) => setName(e.target.value)}
            className="w-full bg-transparent border-none text-lg font-medium text-[#1A1A1A] placeholder-[#B5B5B5] outline-none"
            placeholder="Project name..."
          />
        </div>
      </div>

      <div className="flex flex-wrap items-center gap-3 mb-7">
        <span className="text-base text-[#6B6B6B]">This is a</span>
        <div className="flex bg-[#F5F3ED] rounded-full p-1">
          <button
            type="button"
            className={`px-5 py-2.5 rounded-full text-sm font-semibold transition-all ${type === 'work' ? 'bg-white text-[#1A1A1A] shadow-sm' : 'text-[#6B6B6B] hover:text-[#1A1A1A]'}`}
            onClick={() => setType('work')}
            disabled={isSubmitting}
          >
            Work
          </button>
          <button
            type="button"
            className={`px-5 py-2.5 rounded-full text-sm font-semibold transition-all ${type === 'personal' ? 'bg-white text-[#1A1A1A] shadow-sm' : 'text-[#6B6B6B] hover:text-[#1A1A1A]'}`}
            onClick={() => setType('personal')}
            disabled={isSubmitting}
          >
            Personal
          </button>
        </div>
        <span className="text-base text-[#6B6B6B]">project</span>
      </div>

      <div className="mb-6">
        <label className="block text-xs font-bold text-[#B5B5B5] uppercase tracking-widest mb-3">Brief (optional)</label>
        <textarea
          className="w-full p-5 bg-[#F5F3ED] border-2 border-transparent rounded-2xl text-[15px] text-[#1A1A1A] outline-none resize-none leading-relaxed transition-all focus:bg-white focus:border-[#1A1A1A] placeholder-[#B5B5B5]"
          rows={2}
          value={brief}
          onChange={(e) => setBrief(e.target.value)}
          placeholder="What's this about? What does success look like?"
        />
      </div>

      <div className="mb-6">
        <label className="block text-xs font-bold text-[#B5B5B5] uppercase tracking-widest mb-3">Tasks in mind? (optional)</label>
        <div className="flex flex-col gap-2">
          {tasks.map((t, idx) => (
            <div key={idx} className="flex flex-col gap-1 p-3.5 bg-[#F5F3ED] rounded-xl transition-all focus-within:ring-1 focus-within:ring-[#EBE8E0]">
              <div className="flex items-center gap-3">
                <div className="w-5 h-5 rounded-md border-2 border-[#EBE8E0] bg-white shrink-0" />
                <input
                  className="flex-1 bg-transparent border-none text-[15px] text-[#1A1A1A] outline-none placeholder-[#B5B5B5]"
                  value={t.title}
                  onChange={(e) => updateTask(idx, 'title', e.target.value)}
                  placeholder={idx === 0 ? 'First thing to do...' : 'Next task...'}
                />

                {/* Add Note Button - Only visible if no note content and not explicitly shown */}
                {(!t.note && !t.showNote) && (
                  <button
                    type="button"
                    onClick={() => updateTask(idx, 'showNote', true)}
                    className="text-xs font-medium text-[#B5B5B5] hover:text-[#1A1A1A] transition-colors whitespace-nowrap px-2 py-1 rounded"
                    title="Add a note to this task"
                  >
                    Add note
                  </button>
                )}
              </div>

              {/* Note Input - Visible if note exists OR showNote is true */}
              {(t.note || t.showNote) && (
                <div className="pl-8 flex items-center gap-2 animate-[fadeIn_0.2s_ease-out]">
                  <input
                     className="w-full bg-transparent border-none text-[13px] text-[#6B6B6B] outline-none placeholder-[#B5B5B5]/70"
                     value={t.note}
                     onChange={(e) => updateTask(idx, 'note', e.target.value)}
                     placeholder="Add a note..."
                     autoFocus={t.showNote && !t.note}
                  />
                </div>
              )}

              <div className="pl-8 flex flex-col gap-1 mt-2">
                <span className="text-[11px] font-semibold uppercase tracking-widest text-[#C0C0C0]">Task deadline (optional)</span>
                <div className="flex flex-col sm:flex-row gap-2">
                  <input
                    type="date"
                    className="bg-[#F5F3ED] border border-transparent rounded-xl px-3 py-2 text-sm text-[#1A1A1A] outline-none focus:border-[#1A1A1A] cursor-pointer flex-1"
                    value={t.deadlineDate || ''}
                    onChange={(e) => updateTask(idx, 'deadlineDate', e.target.value)}
                    disabled={isSubmitting}
                  />
                  <input
                    type="time"
                    className="bg-[#F5F3ED] border border-transparent rounded-xl px-3 py-2 text-sm text-[#1A1A1A] outline-none focus:border-[#1A1A1A] cursor-pointer sm:w-32"
                    value={t.deadlineTime || ''}
                    onChange={(e) => updateTask(idx, 'deadlineTime', e.target.value)}
                    disabled={isSubmitting}
                  />
                </div>
              </div>
            </div>
          ))}
          <button
            type="button"
            className="flex items-center gap-2 p-3 bg-transparent border-2 border-dashed border-[#EBE8E0] rounded-xl text-sm font-medium text-[#B5B5B5] hover:border-[#6B6B6B] hover:text-[#6B6B6B] transition-all cursor-pointer w-fit"
            onClick={addTaskRow}
          >
            <span className="font-bold text-lg leading-none">＋</span>
            Add another
          </button>
        </div>
      </div>

      {/* Section 2: Add Details */}
      <div className="flex items-center gap-3 mb-7 mt-8">
        <div className="w-7 h-7 rounded-full bg-[#1A1A1A] text-white text-[13px] font-bold flex items-center justify-center">2</div>
        <span className="text-[13px] font-semibold text-[#6B6B6B] uppercase tracking-widest">Add Details</span>
      </div>

      <div className="flex flex-col gap-8">
        {/* Timeline & Deadline */}
        <div className="flex flex-col gap-3">
          <span className="text-xs font-bold text-[#B5B5B5] uppercase tracking-widest">Timeline</span>
          <div className="flex flex-wrap gap-2">
            {(['Today', 'Week', 'Month', 'Long-term'] as const).map((tVal) => (
              <button
                key={tVal}
                type="button"
                className={`flex-1 min-w-25 py-3.5 px-3 rounded-xl text-sm font-medium transition-all ${
                  timeline === tVal
                    ? 'bg-[#1A1A1A] text-white'
                    : 'bg-[#F5F3ED] text-[#6B6B6B] hover:bg-[#ebe9e1]'
                }`}
                onClick={() => setTimeline(tVal)}
                disabled={isSubmitting}
              >
                {tVal}
              </button>
            ))}
          </div>

          <div className="mt-2">
            <span className="block text-xs font-medium text-[#B5B5B5] mb-2">Deadline (optional)</span>
            <div className="flex items-center gap-2">
              <div className="relative">
                <select
                  className="appearance-none bg-[#F5F3ED] pl-4 pr-8 py-3 rounded-full text-sm font-medium text-[#6B6B6B] outline-none focus:ring-1 focus:ring-[#1A1A1A] cursor-pointer"
                  value={deadlineMonth}
                  onChange={(e) => setDeadlineMonth(e.target.value)}
                  disabled={isSubmitting}
                >
                  <option value="">Month</option>
                  {['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'].map((m, i) => (
                    <option key={m} value={String(i + 1).padStart(2, '0')}>{m}</option>
                  ))}
                </select>
                <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-2 text-[#6B6B6B]">
                  <svg className="fill-current h-4 w-4" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20"><path d="M9.293 12.95l.707.707L15.657 8l-1.414-1.414L10 10.828 5.757 6.586 4.343 8z"/></svg>
                </div>
              </div>

              <div className="relative">
                <select
                  className="appearance-none bg-[#F5F3ED] pl-4 pr-8 py-3 rounded-full text-sm font-medium text-[#6B6B6B] outline-none focus:ring-1 focus:ring-[#1A1A1A] cursor-pointer"
                  value={deadlineDay}
                  onChange={(e) => setDeadlineDay(e.target.value)}
                  disabled={isSubmitting}
                >
                  <option value="">Day</option>
                  {Array.from({ length: 31 }, (_, i) => i + 1).map((d) => (
                    <option key={d} value={String(d).padStart(2, '0')}>{d}</option>
                  ))}
                </select>
                <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-2 text-[#6B6B6B]">
                   <svg className="fill-current h-4 w-4" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20"><path d="M9.293 12.95l.707.707L15.657 8l-1.414-1.414L10 10.828 5.757 6.586 4.343 8z"/></svg>
                </div>
              </div>

              <div className="relative">
                <select
                  className="appearance-none bg-[#F5F3ED] pl-4 pr-8 py-3 rounded-full text-sm font-medium text-[#6B6B6B] outline-none focus:ring-1 focus:ring-[#1A1A1A] cursor-pointer"
                  value={deadlineYear}
                  onChange={(e) => setDeadlineYear(e.target.value)}
                  disabled={isSubmitting}
                >
                  <option value="">Year</option>
                  {yearOptions.map((year) => (
                    <option key={year} value={year}>{year}</option>
                  ))}
                </select>
                <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-2 text-[#6B6B6B]">
                  <svg className="fill-current h-4 w-4" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20"><path d="M9.293 12.95l.707.707L15.657 8l-1.414-1.414L10 10.828 5.757 6.586 4.343 8z"/></svg>
                </div>
              </div>

              <input
                type="time"
                className="bg-[#F5F3ED] w-28 py-3 px-4 rounded-full text-sm font-medium text-[#1A1A1A] outline-none focus:ring-1 focus:ring-[#1A1A1A] text-center placeholder-[#6B6B6B]"
                value={deadlineTime}
                onChange={(e) => setDeadlineTime(e.target.value)}
                disabled={isSubmitting}
              />
            </div>
          </div>
        </div>

        {/* Why are you doing this? - REDESIGNED */}
        <div className="flex flex-col gap-3">
          <span className="text-xs font-bold text-[#B5B5B5] uppercase tracking-widest">Why are you doing this?</span>
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
            {['Make money', 'Creative output', 'Health', 'Joy', 'Family', 'Growth'].map((label) => {
              const isActive = why.includes(label);
              return (
                <button
                  key={label}
                  type="button"
                  className={`relative py-3 px-4 rounded-xl text-sm font-semibold transition-all duration-200 border-2 ${
                    isActive
                      ? 'bg-[#1A1A1A] border-[#1A1A1A] text-white shadow-md transform scale-[1.02]'
                      : 'bg-[#F5F3ED] border-transparent text-[#6B6B6B] hover:border-[#EBE8E0] hover:bg-[#F0EEE6]'
                  }`}
                  onClick={() => toggleWhy(label)}
                  disabled={isSubmitting}
                >
                  <div className="flex items-center justify-center gap-2">
                    {label}
                    {isActive && (
                      <span className="bg-white text-black rounded-full w-4 h-4 flex items-center justify-center text-[10px]">✓</span>
                    )}
                  </div>
                </button>
              );
            })}
          </div>
        </div>

        {/* Who's involved? - REDESIGNED */}
        <div className="flex flex-col gap-3">
          <span className="text-xs font-bold text-[#B5B5B5] uppercase tracking-widest">Who&apos;s involved?</span>
          <div className="self-start bg-[#F5F3ED] p-1.5 rounded-2xl inline-flex gap-1">
            {(['me', 'others'] as const).map((p) => {
               const isActive = people === p;
               return (
                <button
                  key={p}
                  type="button"
                  className={`px-6 py-3 rounded-xl text-sm font-semibold transition-all duration-200 ${
                    isActive
                      ? 'bg-white text-[#1A1A1A] shadow-sm'
                      : 'text-[#6B6B6B] hover:text-[#4A4A4A]'
                  }`}
                  onClick={() => setPeople(p)}
                  disabled={isSubmitting}
                >
                  {p === 'me' ? 'Just me' : 'Others too'}
                </button>
               );
            })}
          </div>

          {/* Expanded "Others" section */}
          {people === 'others' && (
            <div className="mt-2 p-5 bg-[#FAFAF8] border border-[#EBE8E0] rounded-2xl animate-[fadeIn_0.2s_ease-out]">
              <div className="flex flex-col gap-3">
                 <span className="text-xs font-semibold text-[#6B6B6B] uppercase tracking-wide">Team Members</span>

                 <div className="flex flex-col md:flex-row gap-2">
                   <input
                      className="flex-1 bg-white border border-[#EBE8E0] rounded-xl px-4 py-3 text-sm text-[#1A1A1A] outline-none focus:border-[#1A1A1A] placeholder-[#B5B5B5] transition-colors"
                      placeholder="Name"
                      value={otherName}
                      onChange={e => setOtherName(e.target.value)}
                      disabled={isSubmitting}
                   />
                   <input
                      className="flex-1 bg-white border border-[#EBE8E0] rounded-xl px-4 py-3 text-sm text-[#1A1A1A] outline-none focus:border-[#1A1A1A] placeholder-[#B5B5B5] transition-colors"
                      placeholder="Role or Notes (optional)"
                      value={otherNote}
                      onChange={e => setOtherNote(e.target.value)}
                      onKeyDown={e => e.key === 'Enter' && handleAddPerson()}
                      disabled={isSubmitting}
                   />
                   <button
                     type="button"
                     onClick={handleAddPerson}
                     className="bg-[#1A1A1A] text-white px-5 py-3 rounded-xl text-sm font-bold hover:bg-black transition-colors shrink-0"
                     disabled={isSubmitting}
                   >
                     Add
                   </button>
                 </div>

                 {othersList.length > 0 && (
                   <div className="grid grid-cols-1 gap-2 mt-2">
                      {othersList.map((p, i) => (
                        <div key={i} className="flex items-center justify-between bg-white border border-[#EBE8E0] p-3 rounded-xl">
                           <div className="flex flex-col">
                              <span className="text-sm font-bold text-[#1A1A1A]">{p.name}</span>
                              {p.note && <span className="text-xs text-[#6B6B6B]">{p.note}</span>}
                           </div>
                           <button onClick={() => removePerson(i)} type="button" className="text-[#B5B5B5] hover:text-red-500 p-2">
                              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="w-5 h-5">
                                <path d="M6.28 5.22a.75.75 0 00-1.06 1.06L8.94 10l-3.72 3.72a.75.75 0 101.06 1.06L10 11.06l3.72 3.72a.75.75 0 101.06-1.06L11.06 10l3.72-3.72a.75.75 0 00-1.06-1.06L10 8.94 6.28 5.22z" />
                              </svg>
                           </button>
                        </div>
                      ))}
                   </div>
                 )}
              </div>
            </div>
          )}
        </div>

        {/* Files & Links - REDESIGNED */}
        <div className="flex flex-col gap-3">
          <div className="flex justify-between items-end">
            <span className="text-xs font-bold text-[#B5B5B5] uppercase tracking-widest">Files & Links (optional)</span>
            <span className="text-xs text-[#B5B5B5]">
              {files.length} file{files.length !== 1 ? 's' : ''}, {links.length} link{links.length !== 1 ? 's' : ''}
            </span>
          </div>

          <div className="border border-[#EBE8E0] rounded-2xl p-5 bg-[#FAFAF8]">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">

              {/* Dropzone Section */}
              <div
                className={`relative border-2 border-dashed rounded-xl flex flex-col items-center justify-center p-6 text-center transition-all cursor-pointer min-h-40
                  ${isDragging ? 'border-blue-400 bg-blue-50' : 'border-[#EBE8E0] bg-white hover:border-[#D1D1D1] hover:bg-[#FDFDFD]'}
                `}
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
                onClick={() => fileInputRef.current?.click()}
              >
                 <input
                   type="file"
                   multiple
                   ref={fileInputRef}
                   className="hidden"
                   onChange={(e) => addFiles(e.target.files)}
                   disabled={isSubmitting}
                  />
                 <div className="w-10 h-10 mb-3 rounded-full bg-[#F5F3ED] flex items-center justify-center text-[#6B6B6B]">
                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-5 h-5">
                      <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5" />
                    </svg>
                 </div>
                 <p className="text-sm font-semibold text-[#1A1A1A]">Upload Files</p>
                 <p className="text-xs text-[#6B6B6B] mt-1">Drag & drop or click to browse</p>
              </div>

              {/* Links Section */}
              <div className="flex flex-col gap-3">
                 <div className="bg-white border border-[#EBE8E0] rounded-xl p-4 h-full flex flex-col">
                    <span className="text-xs font-semibold text-[#6B6B6B] mb-3 uppercase tracking-wide">Add Links</span>
                    <div className="flex gap-2 mb-3">
                      <input
                        className="flex-1 bg-[#F5F3ED] rounded-lg px-3 py-2 text-sm text-[#1A1A1A] outline-none focus:ring-1 focus:ring-[#1A1A1A] placeholder-[#B5B5B5]"
                        placeholder="https://"
                        value={linkInput}
                        onChange={(e) => setLinkInput(e.target.value)}
                        onKeyDown={(e) => e.key === 'Enter' && handleAddLink()}
                      />
                      <button
                        type="button"
                        onClick={handleAddLink}
                        className="bg-[#1A1A1A] text-white px-3 py-2 rounded-lg text-xs font-bold uppercase hover:bg-black transition-colors"
                      >
                        Add
                      </button>
                    </div>

                    {/* Links List - Simple Scrollable */}
                    <div className="flex-1 overflow-y-auto min-h-25 flex flex-col gap-2">
                       {links.length === 0 && (
                         <div className="text-xs text-[#B5B5B5] text-center italic mt-2">No links added yet</div>
                       )}
                       {links.map((link, i) => (
                         <div key={i} className="flex items-center justify-between bg-[#F5F3ED] px-3 py-2 rounded-lg group">
                            <span className="text-xs text-[#1A1A1A] truncate max-w-37" title={link}>{link}</span>
                            <button onClick={() => removeLink(i)} type="button" className="text-[#B5B5B5] hover:text-red-500">
                              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="w-4 h-4">
                                <path d="M6.28 5.22a.75.75 0 00-1.06 1.06L8.94 10l-3.72 3.72a.75.75 0 101.06 1.06L10 11.06l3.72 3.72a.75.75 0 101.06-1.06L11.06 10l3.72-3.72a.75.75 0 00-1.06-1.06L10 8.94 6.28 5.22z" />
                              </svg>
                            </button>
                         </div>
                       ))}
                    </div>
                 </div>
              </div>
            </div>

            {/* Uploaded Files List */}
            {files.length > 0 && (
              <div className="mt-4 flex flex-wrap gap-2 pt-4 border-t border-[#EBE8E0]">
                {files.map((file, idx) => (
                  <div key={`${file.name}-${idx}`} className="flex items-center gap-2 pl-3 pr-2 py-1.5 bg-white border border-[#EBE8E0] rounded-lg shadow-sm">
                    <span className="text-xs font-medium text-[#1A1A1A] max-w-50 truncate">{file.name}</span>
                    <button
                      type="button"
                      onClick={() => removeFile(idx)}
                      className="p-1 hover:bg-[#F5F3ED] rounded-md text-[#B5B5B5] hover:text-[#1A1A1A] transition-colors"
                    >
                      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="w-4 h-4">
                        <path d="M6.28 5.22a.75.75 0 00-1.06 1.06L8.94 10l-3.72 3.72a.75.75 0 101.06 1.06L10 11.06l3.72 3.72a.75.75 0 101.06-1.06L11.06 10l3.72-3.72a.75.75 0 00-1.06-1.06L10 8.94 6.28 5.22z" />
                      </svg>
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

      <div className="mt-10 pt-6 border-t border-[#F5F3ED] flex justify-end">
        <button
          type="button"
          className={`flex items-center gap-2 px-8 py-4 rounded-full text-[15px] font-bold text-white transition-all transform hover:-translate-y-0.5
            ${canCreate ? 'bg-[#FF6129] shadow-lg shadow-orange-200 cursor-pointer' : 'bg-[#E0E0E0] cursor-not-allowed'}
          `}
          disabled={!canCreate}
          onClick={handleCreate}
        >
          {isSubmitting ? (
            <>
              <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"></path>
              </svg>
              Creating...
            </>
          ) : (
            'Create Project'
          )}
        </button>
      </div>
    </div>
  );
}
