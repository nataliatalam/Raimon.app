'use client';

import React, { useState, useRef, useEffect } from 'react';
import { Send, Smile, Plus, Brain, Sparkles, Tag, HelpCircle, ChevronDown, Link2, File, Paperclip, Cloud } from 'lucide-react';
import { useSession } from './providers/SessionProvider';
import { apiFetch } from '../../lib/api-client';
import type { ApiSuccessResponse, ProjectApiRecord } from '../../types/api';

const CATEGORIES = ['Errands', 'Social', 'Genius', 'My Projects'] as const;
type Category = (typeof CATEGORIES)[number];

const CATEGORY_INFO: Record<Category, string> = {
  Errands: 'Life maintenance: groceries, cleaning, bills.',
  Social: 'Connections: replies, calls, gift ideas.',
  Genius: 'Big ideas: apps, business, art, or "shower thoughts".',
  'My Projects': 'Work tasks: specific to your active project boards.',
};

const BrainDump: React.FC = () => {
  const { session, status } = useSession();
  const [isExpanded, setIsExpanded] = useState(false);
  const [showHelp, setShowHelp] = useState(false);
  const [thought, setThought] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<Category | null>(null);
  const [projects, setProjects] = useState<{ id: string; name: string }[]>([]);
  const [selectedProject, setSelectedProject] = useState('');
  const [isSuccess, setIsSuccess] = useState(false);
  const [isDragging, setIsDragging] = useState(false);
  const [attachments, setAttachments] = useState<{ name: string; type: 'file' | 'link' }[]>([]);

  const inputRef = useRef<HTMLTextAreaElement>(null);

  // Fetch user's projects
  useEffect(() => {
    if (status !== 'ready' || !session.accessToken) return;

    async function fetchProjects() {
      try {
        const response = await apiFetch<ApiSuccessResponse<{ projects: ProjectApiRecord[] }>>('/api/projects');
        const projectList = response.data.projects.map(p => ({ id: p.id, name: p.name }));
        setProjects(projectList);
        if (projectList.length > 0 && !selectedProject) {
          setSelectedProject(projectList[0].name);
        }
      } catch {
        // Silently fail - projects dropdown will be empty
      }
    }

    fetchProjects();
  }, [status, session.accessToken, selectedProject]);

  useEffect(() => {
    if (isExpanded && inputRef.current) {
      inputRef.current.focus();
    }
  }, [isExpanded]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!thought.trim() && attachments.length === 0) return;

    setThought('');
    setSelectedCategory(null);
    setAttachments([]);
    setIsSuccess(true);
    setTimeout(() => {
      setIsSuccess(false);
      setIsExpanded(false);
    }, 2000);
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    const files = Array.from(e.dataTransfer.files) as File[];
    const links = e.dataTransfer.getData('text/uri-list');

    if (files.length > 0) {
      setAttachments((prev) => [...prev, ...files.map((f) => ({ name: f.name, type: 'file' as const }))]);
    }
    if (links) {
      setAttachments((prev) => [...prev, { name: links.split('\n')[0], type: 'link' as const }]);
    }
  };

  return (
    <div className="relative flex items-center h-10">
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className={`group flex items-center gap-3 h-10 px-1 pr-4 rounded-full border transition-all duration-500 active:scale-95 ${
          isExpanded
            ? 'bg-black border-black shadow-xl shadow-black/10'
            : 'bg-white border-zinc-100 hover:shadow-xl hover:shadow-black/5'
        }`}
      >
        <div
          className={`h-8 w-8 rounded-full flex items-center justify-center transition-all duration-500 ${
            isExpanded
              ? 'bg-[#FF6B00] text-white rotate-12'
              : 'bg-black text-white group-hover:bg-[#FF6B00] group-hover:rotate-12'
          }`}
        >
          <Brain size={14} />
        </div>

        <div className="flex flex-col items-start">
          <span
            className={`text-[9px] font-black uppercase tracking-[0.1em] leading-none ${
              isExpanded ? 'text-white' : 'text-zinc-800'
            }`}
          >
            Brain Dump
          </span>
          <span
            className={`text-[7px] font-bold uppercase tracking-tighter leading-none mt-0.5 ${
              isExpanded ? 'text-white/50' : 'text-zinc-400'
            }`}
          >
            Park your thoughts
          </span>
        </div>
      </button>

      {isExpanded && (
        <div className="absolute top-full left-0 mt-4 animate-in zoom-in-95 slide-in-from-top-2 fade-in duration-300 z-[100]">
          <div
            className={`
            relative flex flex-col bg-white border-2 border-zinc-900 rounded-[2.5rem] p-5 shadow-[0_50px_100px_rgba(0,0,0,0.3)] transition-all duration-500 w-[420px]
            ${isSuccess ? 'border-[#FF6B00] bg-orange-50/20' : ''}
          `}
          >
            {isSuccess && (
              <div className="absolute inset-0 z-10 flex flex-col items-center justify-center bg-white/95 rounded-[2.5rem] animate-in fade-in duration-300">
                <Smile size={40} className="text-[#FF6B00] mb-3 animate-bounce" />
                <p className="text-lg font-black text-zinc-900 uppercase tracking-tighter">Dumped & Safe.</p>
                <p className="text-[10px] font-bold text-[#FF6B00] mt-1">Returning to deep focus...</p>
              </div>
            )}

            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2.5">
                <div className="h-8 w-8 rounded-xl bg-[#FF6B00]/10 text-[#FF6B00] flex items-center justify-center">
                  <Sparkles size={16} />
                </div>
                <div>
                  <h3 className="text-xs font-black text-zinc-900 uppercase tracking-widest">Brain Dump</h3>
                  <p className="text-[9px] font-medium text-zinc-400">Clear your mind instantly.</p>
                </div>
              </div>
              <button
                onClick={() => setIsExpanded(false)}
                className="h-8 w-8 rounded-full bg-zinc-50 text-zinc-400 hover:bg-zinc-100 transition-all flex items-center justify-center"
              >
                <Plus size={16} className="rotate-45" />
              </button>
            </div>

            <form onSubmit={handleSubmit}>
              <div className="relative">
                <textarea
                  ref={inputRef}
                  value={thought}
                  onChange={(e) => setThought(e.target.value)}
                  placeholder="What's trying to distract you?"
                  className="w-full bg-zinc-50 outline-none rounded-2xl p-4 text-sm font-medium text-zinc-800 placeholder:text-zinc-300 min-h-[80px] resize-none focus:ring-2 focus:ring-[#FF6B00]/20 transition-all border-2 border-transparent"
                />
              </div>

              {/* Drag & Drop Section */}
              <div className="mt-4">
                <div className="flex items-center gap-2 mb-2">
                  <Paperclip size={10} className="text-zinc-400" />
                  <span className="text-[9px] font-black text-zinc-400 uppercase tracking-widest">
                    Context / Attachments
                  </span>
                </div>

                <div
                  onDragOver={handleDragOver}
                  onDragLeave={handleDragLeave}
                  onDrop={handleDrop}
                  className={`
                    relative min-h-[60px] rounded-2xl border-2 border-dashed transition-all duration-300 flex flex-col items-center justify-center gap-1 p-3
                    ${
                      isDragging
                        ? 'border-[#FF6B00] bg-[#FF6B00]/5 scale-[1.02]'
                        : 'border-zinc-100 bg-zinc-50/50 hover:bg-zinc-50 hover:border-zinc-200'
                    }
                  `}
                >
                  {attachments.length === 0 ? (
                    <>
                      <Cloud size={16} className={`${isDragging ? 'text-[#FF6B00] animate-bounce' : 'text-zinc-300'}`} />
                      <span className="text-[8px] font-bold text-zinc-400 uppercase tracking-widest text-center">
                        Drop files or links here to process later
                      </span>
                    </>
                  ) : (
                    <div className="flex flex-wrap gap-1.5 w-full">
                      {attachments.map((at, i) => (
                        <div
                          key={i}
                          className="flex items-center gap-2 px-2.5 py-1.5 bg-white border border-zinc-100 rounded-full shadow-sm animate-in zoom-in-95"
                        >
                          {at.type === 'link' ? (
                            <Link2 size={10} className="text-blue-500" />
                          ) : (
                            <File size={10} className="text-indigo-500" />
                          )}
                          <span className="text-[8px] font-black text-zinc-600 truncate max-w-[140px] uppercase tracking-tighter">
                            {at.name}
                          </span>
                          <button
                            type="button"
                            onClick={() => setAttachments((prev) => prev.filter((_, idx) => idx !== i))}
                            className="text-zinc-300 hover:text-red-500 transition-colors"
                          >
                            <Plus size={10} className="rotate-45" />
                          </button>
                        </div>
                      ))}
                      <div className="h-7 px-3 border border-dashed border-zinc-200 rounded-full flex items-center justify-center gap-1.5 group cursor-pointer hover:border-[#FF6B00] transition-colors">
                        <Plus size={8} className="text-zinc-300 group-hover:text-[#FF6B00]" />
                        <span className="text-[7px] font-black text-zinc-300 group-hover:text-[#FF6B00] uppercase tracking-widest">
                          More
                        </span>
                      </div>
                    </div>
                  )}
                </div>
              </div>

              <div className="flex flex-col gap-3 mt-5">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="flex items-center gap-2">
                      <Tag size={10} className="text-zinc-400" />
                      <span className="text-[9px] font-black text-zinc-400 uppercase tracking-widest">Categorize</span>
                    </div>
                    <button
                      type="button"
                      onClick={() => setShowHelp(!showHelp)}
                      className={`
                        h-7 w-7 rounded-xl flex items-center justify-center transition-all duration-300 shadow-sm
                        ${
                          showHelp
                            ? 'bg-[#FF6B00] text-white rotate-12 scale-110'
                            : 'bg-black text-white hover:bg-[#FF6B00] hover:rotate-12'
                        }
                      `}
                      title="What do these mean?"
                    >
                      <HelpCircle size={15} />
                    </button>
                  </div>
                </div>

                {showHelp && (
                  <div className="p-4 bg-zinc-900 rounded-[1.5rem] animate-in slide-in-from-top-2 duration-400 shadow-2xl">
                    <div className="grid grid-cols-2 gap-4">
                      {CATEGORIES.map((cat) => (
                        <div key={cat} className="flex flex-col group/item">
                          <span className="text-[9px] font-black text-[#FF6B00] uppercase tracking-widest mb-1 group-hover/item:translate-x-1 transition-transform">
                            {cat}
                          </span>
                          <p className="text-[8px] font-medium text-white/50 leading-tight group-hover/item:text-white/80 transition-colors">
                            {CATEGORY_INFO[cat]}
                          </p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                <div className="flex flex-wrap gap-1.5 mt-1">
                  {CATEGORIES.map((cat) => (
                    <button
                      key={cat}
                      type="button"
                      onClick={() => setSelectedCategory(cat)}
                      className={`
                        px-4 py-2 rounded-full text-[9px] font-black uppercase tracking-widest transition-all
                        ${
                          selectedCategory === cat
                            ? 'bg-black text-white shadow-lg scale-105'
                            : 'bg-zinc-100 text-zinc-500 hover:bg-zinc-200'
                        }
                      `}
                    >
                      {cat}
                    </button>
                  ))}
                </div>

                {selectedCategory === 'My Projects' && (
                  <div className="relative mt-1 animate-in slide-in-from-top-2 duration-300">
                    <div className="absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none">
                      <div className="w-1.5 h-1.5 rounded-full bg-[#FF6B00]" />
                    </div>
                    <select
                      value={selectedProject}
                      onChange={(e) => setSelectedProject(e.target.value)}
                      className="w-full bg-zinc-50 border-2 border-zinc-100 rounded-full pl-7 pr-10 py-2.5 text-[10px] font-black uppercase tracking-widest appearance-none focus:border-[#FF6B00] outline-none cursor-pointer"
                    >
                      {projects.length === 0 ? (
                        <option value="">No projects available</option>
                      ) : (
                        projects.map((p) => (
                          <option key={p.id} value={p.name}>
                            {p.name}
                          </option>
                        ))
                      )}
                    </select>
                    <div className="absolute right-4 top-1/2 -translate-y-1/2 pointer-events-none">
                      <ChevronDown size={12} className="text-zinc-400" />
                    </div>
                  </div>
                )}
              </div>

              <div className="mt-6 flex items-center justify-between pt-4 border-t border-zinc-100">
                <p className="text-[9px] font-medium text-zinc-400 leading-tight max-w-[150px]">
                  Raimon will process these items for you later.
                </p>
                <button
                  type="submit"
                  disabled={!thought.trim() && attachments.length === 0}
                  className="px-6 py-2.5 rounded-full bg-[#FF6B00] text-white font-black text-[10px] uppercase tracking-[0.2em] hover:bg-black transition-all active:scale-95 disabled:opacity-30 shadow-lg flex items-center gap-2"
                >
                  <Send size={12} />
                  Complete Dump
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default BrainDump;
