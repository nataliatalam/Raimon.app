'use client';

import React, { useState, useEffect, useMemo } from 'react';
import { Task } from './TasksPage';

interface ProjectFilterProps {
  allTasks: Task[];
  selectedProjects: string[];
  onChange: (projects: string[]) => void;
}

type FilterTab = 'all' | 'work' | 'personal';

export default function ProjectFilter({ allTasks, selectedProjects, onChange }: ProjectFilterProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [activeTab, setActiveTab] = useState<FilterTab>('all');
  const [pendingSelection, setPendingSelection] = useState<string[]>([]);

  // 1. Derive unique projects (memoized to prevent infinite loops)
  const uniqueProjects = useMemo(
    () => Array.from(new Set(allTasks.map((t) => t.project))).sort(),
    [allTasks]
  );

  // 2. Mock Categorization Logic (memoized)
  const workProjects = useMemo(
    () => uniqueProjects.filter(p => {
      const lower = p.toLowerCase();
      return !lower.includes('personal') && !lower.includes('life') && !lower.includes('home');
    }),
    [uniqueProjects]
  );

  const personalProjects = useMemo(
    () => uniqueProjects.filter(p => {
      const lower = p.toLowerCase();
      return lower.includes('personal') || lower.includes('life') || lower.includes('home');
    }),
    [uniqueProjects]
  );

  const isAllSelected = selectedProjects.length === 0;

  // 3. Sync state when modal opens
  useEffect(() => {
    if (!isOpen) return;

    if (isAllSelected) {
      setActiveTab('all');
      setPendingSelection([]);
    } else {
      const hasWork = selectedProjects.some(p => workProjects.includes(p));
      const hasPersonal = selectedProjects.some(p => personalProjects.includes(p));

      if (hasWork && !hasPersonal) {
        setActiveTab('work');
        setPendingSelection(selectedProjects);
      } else if (!hasWork && hasPersonal) {
        setActiveTab('personal');
        setPendingSelection(selectedProjects);
      } else {
        setActiveTab('all');
        setPendingSelection([]);
      }
    }
  }, [isOpen, isAllSelected, selectedProjects, workProjects, personalProjects]);

  const handleTabSwitch = (tab: FilterTab) => {
    setActiveTab(tab);
    if (tab === 'all') setPendingSelection([]);
    else if (tab === 'work') setPendingSelection([...workProjects]);
    else if (tab === 'personal') setPendingSelection([...personalProjects]);
  };

  const toggleProject = (project: string) => {
    if (pendingSelection.includes(project)) {
      setPendingSelection(prev => prev.filter(p => p !== project));
    } else {
      setPendingSelection(prev => [...prev, project]);
    }
  };

  const handleSave = () => {
    if (activeTab === 'all') onChange([]);
    else onChange(pendingSelection);
    setIsOpen(false);
  };

  const visibleProjects = activeTab === 'work' ? workProjects : activeTab === 'personal' ? personalProjects : [];

  // Logic for the Collapsed Card Text
  let title = "All Projects";

  const currentHasWork = selectedProjects.some(p => workProjects.includes(p));
  const currentHasPersonal = selectedProjects.some(p => personalProjects.includes(p));

  if (!isAllSelected) {
    if (currentHasWork && !currentHasPersonal) {
      title = "Work Mode";
    } else if (!currentHasWork && currentHasPersonal) {
      title = "Personal";
    } else {
      title = "Custom";
    }
  }

  // --- Render Helpers ---

  // Reusable Collapsed Button Content - Pill Layout
  const CollapsedButtonContent = () => (
    <div className="flex items-center gap-3">
      <span className="text-gray-900 text-sm font-bold whitespace-nowrap">
        {title}
      </span>

      {/* Divider */}
      <span className="w-px h-3 bg-gray-300" />

      <div className="flex items-center gap-1.5 text-orange group-hover:text-orange/80 transition-colors">
        <span className="text-[11px] font-bold tracking-widest uppercase">
          Edit
        </span>
        <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
          <path d="M5 12h14M12 5l7 7-7 7"/>
        </svg>
      </div>
    </div>
  );

  return (
    // Relative container to anchor the absolute Expanded Card
    <div className="relative z-40 inline-block">

      {/*
        GHOST ELEMENT for layout stability:
        Always render the collapsed button "in flow".
        When open, we hide it visually (opacity-0) so the Absolute Card can take its place visually
        without the parent container collapsing its height/width.
      */}
      <div className={`${isOpen ? 'opacity-0 pointer-events-none' : 'opacity-100'}`}>
         <button
            onClick={() => setIsOpen(true)}
            className="group bg-white border border-gray-200 rounded-full px-5 py-2.5 shadow-sm hover:shadow-md hover:border-orange/30 transition-all duration-300"
          >
            <CollapsedButtonContent />
         </button>
      </div>

      {/* Expanded Modal UI - Absolute positioned relative to this container */}
      {isOpen && (
        <>
          {/* Backdrop */}
          <div className="fixed inset-0 bg-black/10 backdrop-blur-sm z-40" onClick={() => setIsOpen(false)} />

          {/* Card - Anchored top-left to expand FROM the button's position */}
          <div className="absolute top-0 left-0 z-50 w-72 bg-[#f5f3ed] border-2 border-orange rounded-3xl shadow-2xl overflow-hidden animate-in fade-in zoom-in-95 duration-200 flex flex-col max-h-[80vh]">

            {/* Header */}
            <div className="p-5 pb-3">
              <div className="flex items-center justify-between mb-5">
                <h2 className="text-gray-900 text-2xl font-light tracking-tight leading-none">Focus Mode</h2>
                <button
                  onClick={() => setIsOpen(false)}
                  className="text-gray-400 hover:text-gray-900 transition-colors"
                >
                  <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <line x1="18" y1="6" x2="6" y2="18"></line>
                    <line x1="6" y1="6" x2="18" y2="18"></line>
                  </svg>
                </button>
              </div>

              {/* TABS */}
              <div className="grid grid-cols-3 gap-1 bg-white p-1 rounded-xl border border-orange/10">
                {(['all', 'work', 'personal'] as const).map((tab) => {
                  const isActive = activeTab === tab;
                  const label = tab === 'all' ? 'All' : tab.charAt(0).toUpperCase() + tab.slice(1);
                  return (
                    <button
                      key={tab}
                      onClick={() => handleTabSwitch(tab)}
                      className={`
                        py-1.5 text-[10px] font-bold uppercase tracking-wider rounded-lg transition-all duration-200
                        ${isActive
                          ? 'bg-orange text-white shadow-sm'
                          : 'text-gray-500 hover:text-gray-900 hover:bg-[#f5f3ed]'
                        }
                      `}
                    >
                      {label}
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Content Area */}
            <div className="flex-1 overflow-y-auto px-2">
              {activeTab === 'all' ? (
                <div className="px-4 py-8 text-center">
                  <div className="inline-flex items-center justify-center w-10 h-10 rounded-full bg-orange/10 mb-3 text-orange">
                    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M22 12h-4l-3 9L9 3l-3 9H2"/>
                    </svg>
                  </div>
                  <p className="text-gray-900 text-sm font-medium mb-1">All Projects</p>
                  <p className="text-[11px] text-gray-500 leading-relaxed">
                    Viewing all tasks.
                  </p>
                </div>
              ) : (
                <div className="px-2 pb-4 space-y-1">
                  {visibleProjects.length === 0 ? (
                    <div className="p-4 text-center text-gray-500 text-xs">
                      No {activeTab} projects found.
                    </div>
                  ) : (
                    visibleProjects.map((project) => {
                      const isChecked = pendingSelection.includes(project);
                      return (
                        <button
                          key={project}
                          onClick={() => toggleProject(project)}
                          className={`w-full text-left px-3 py-2.5 rounded-xl flex items-center gap-3 transition-colors ${
                            isChecked ? 'bg-orange/10' : 'hover:bg-black/5'
                          }`}
                        >
                          <div className={`
                            w-4 h-4 rounded border flex items-center justify-center transition-colors shrink-0
                            ${isChecked
                              ? 'bg-orange border-orange text-white'
                              : 'border-gray-300 bg-transparent'
                            }
                          `}>
                            {isChecked && (
                              <svg xmlns="http://www.w3.org/2000/svg" width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="4" strokeLinecap="round" strokeLinejoin="round">
                                <polyline points="20 6 9 17 4 12"></polyline>
                              </svg>
                            )}
                          </div>
                          <span className={`text-xs font-medium truncate ${isChecked ? 'text-gray-900' : 'text-gray-500'}`}>
                            {project}
                          </span>
                        </button>
                      );
                    })
                  )}
                </div>
              )}
            </div>

            {/* Footer / Save Button */}
            <div className="p-3 border-t border-orange/10 bg-[#f5f3ed]">
              <button
                onClick={handleSave}
                className="w-full py-2.5 px-4 bg-orange hover:bg-orange/90 text-white text-sm font-bold rounded-xl transition-colors shadow-lg shadow-orange/20"
              >
                Save
              </button>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
