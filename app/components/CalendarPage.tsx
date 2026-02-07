'use client';

import React, { useState, useEffect, useCallback, useRef, useMemo } from 'react';
import { useSession } from './providers/SessionProvider';
import { apiFetch, ApiError } from '../../lib/api-client';
import type { ApiSuccessResponse, ProjectApiRecord } from '../../types/api';
import { CalendarView, CalendarEvent, CalendarProject } from './calendar/types';
import CalendarHeader from './calendar/CalendarHeader';
import CalendarGrid from './calendar/CalendarGrid';
import GuideDrawer from './calendar/GuideDrawer';
import ItemDetailModal from './calendar/ItemDetailModal';

// Local storage key for events
const EVENTS_STORAGE_KEY = 'raimon_calendar_events';

function generateId(): string {
  return `evt_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
}

function mapProjectToCalendarProject(record: ProjectApiRecord): CalendarProject {
  return {
    id: record.id,
    name: record.name,
    category: record.icon === 'personal' ? 'PERSONAL' : 'WORK',
  };
}

// Load events from localStorage
function loadEventsFromStorage(): CalendarEvent[] {
  if (typeof window === 'undefined') return [];
  try {
    const stored = localStorage.getItem(EVENTS_STORAGE_KEY);
    if (!stored) return [];
    const parsed = JSON.parse(stored);
    return parsed.map((e: Record<string, unknown>) => ({
      ...e,
      startTime: new Date(e.startTime as string),
      endTime: new Date(e.endTime as string),
      source: (e.source as CalendarEvent['source']) ?? 'manual',
    }));
  } catch {
    return [];
  }
}

// Save events to localStorage
function saveEventsToStorage(events: CalendarEvent[]): void {
  if (typeof window === 'undefined') return;
  try {
    localStorage.setItem(EVENTS_STORAGE_KEY, JSON.stringify(events));
  } catch {
    // Ignore storage errors
  }
}

export default function CalendarPage() {
  const { session, status } = useSession();
  const [view, setView] = useState<CalendarView>(CalendarView.DAY);
  const [currentDate, setCurrentDate] = useState(new Date());
  const [userEvents, setUserEvents] = useState<CalendarEvent[]>([]);
  const [deadlineEvents, setDeadlineEvents] = useState<CalendarEvent[]>([]);
  const [projects, setProjects] = useState<CalendarProject[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [isGuideOpen, setIsGuideOpen] = useState(false);
  const [selectedItem, setSelectedItem] = useState<CalendarEvent | null>(null);
  const [isNewEvent, setIsNewEvent] = useState(false);
  const timelineWrapperRef = useRef<HTMLDivElement | null>(null);
  const [timelineHeight, setTimelineHeight] = useState<number | null>(null);

  const buildDeadlineEvents = useCallback((records: ProjectApiRecord[]): CalendarEvent[] => {
    const results: CalendarEvent[] = [];

    const buildRange = (value: string) => {
      const isoValue = value.includes('T') ? value : `${value}T09:00:00`;
      const start = new Date(isoValue);
      if (Number.isNaN(start.getTime())) return null;
      const end = new Date(start);
      end.setHours(end.getHours() + 1);
      return { start, end };
    };

    records.forEach((record) => {
      const category: CalendarEvent['category'] = record.icon === 'personal' ? 'PERSONAL' : 'WORK';

      const projectDeadline = record.target_end_date ?? record.deadline ?? null;
      if (projectDeadline) {
        const range = buildRange(projectDeadline);
        if (range) {
          results.push({
            id: `project-deadline-${record.id}`,
            title: `${record.name} deadline`,
            startTime: range.start,
            endTime: range.end,
            project: record.name,
            projectId: record.id,
            category,
            source: 'project-deadline',
            relatedId: record.id,
          });
        }
      }

      (record.task_deadlines ?? []).forEach((task) => {
        if (!task.deadline || task.status === 'completed') return;
        const range = buildRange(task.deadline);
        if (!range) return;
        results.push({
          id: `task-deadline-${task.id}`,
          title: `${task.title} due`,
          startTime: range.start,
          endTime: range.end,
          project: record.name,
          projectId: record.id,
          category,
          source: 'task-deadline',
          relatedId: task.id ?? undefined,
        });
      });
    });

    return results;
  }, []);

  // Fetch projects from API
  const fetchProjects = useCallback(async () => {
    try {
      const response = await apiFetch<ApiSuccessResponse<{ projects: ProjectApiRecord[] }>>(
        '/api/projects?include_task_deadlines=true'
      );
      const mapped = response.data.projects.map(mapProjectToCalendarProject);
      setProjects(mapped);
      setDeadlineEvents(buildDeadlineEvents(response.data.projects));
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError('Failed to load projects');
      }
    }
  }, [buildDeadlineEvents]);

  // Load events from storage on mount and ensure today's date
  useEffect(() => {
    const storedEvents = loadEventsFromStorage();
    setUserEvents(storedEvents);
    // Ensure we're on today's date when calendar opens
    setCurrentDate(new Date());
    setLoading(false);
  }, []);

  // Fetch projects when session is ready
  useEffect(() => {
    if (status === 'ready' && session.accessToken) {
      fetchProjects();
    }
  }, [status, session.accessToken, fetchProjects]);

  // Save events to storage whenever they change
  useEffect(() => {
    if (!loading) {
      saveEventsToStorage(userEvents);
    }
  }, [userEvents, loading]);

  const events = useMemo(() => [...userEvents, ...deadlineEvents], [userEvents, deadlineEvents]);

  const handleSlotClick = (time: Date) => {
    const endTime = new Date(time);
    endTime.setHours(endTime.getHours() + 1);

    const newEvent: CalendarEvent = {
      id: generateId(),
      title: '',
      startTime: time,
      endTime: endTime,
      category: 'OTHER',
      project: 'Other',
      source: 'manual',
    };

    setSelectedItem(newEvent);
    setIsNewEvent(true);
  };

  const handleItemClick = (item: CalendarEvent) => {
    if (item.source && item.source !== 'manual') return;
    setSelectedItem(item);
    setIsNewEvent(false);
  };

  const handleCloseModal = () => {
    setSelectedItem(null);
    setIsNewEvent(false);
  };

  const handleSaveEvent = (updatedEvent: CalendarEvent) => {
    const manualEvent = { ...updatedEvent, source: 'manual' } as CalendarEvent;
    setUserEvents(prev => {
      const exists = prev.find(e => e.id === manualEvent.id);
      if (exists) {
        return prev.map(e => (e.id === manualEvent.id ? manualEvent : e));
      }
      return [...prev, manualEvent];
    });
    handleCloseModal();
  };

  const handleDeleteEvent = (id: string) => {
    setUserEvents(prev => prev.filter(e => e.id !== id));
    handleCloseModal();
  };

  useEffect(() => {
    if (typeof window === 'undefined') return;
    let frame = 0;

    const updateHeight = () => {
      if (!timelineWrapperRef.current) return;
      const rect = timelineWrapperRef.current.getBoundingClientRect();
      const available = window.innerHeight - rect.top - 24; // keep bottom padding
      setTimelineHeight(Math.max(available, 320));
    };

    const handleResize = () => {
      cancelAnimationFrame(frame);
      frame = window.requestAnimationFrame(updateHeight);
    };

    updateHeight();
    window.addEventListener('resize', handleResize);
    window.addEventListener('scroll', handleResize, true);

    return () => {
      window.removeEventListener('resize', handleResize);
      window.removeEventListener('scroll', handleResize, true);
      cancelAnimationFrame(frame);
    };
  }, [view, isGuideOpen]);

  if (status === 'loading' || loading) {
    return (
      <div className="flex items-center justify-center h-full min-h-[400px]">
        <div className="text-center">
          <div className="w-8 h-8 border-2 border-orange-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-sm text-gray-400 font-medium">Loading calendar...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full min-h-0">
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-2xl mb-4 text-sm">
          {error}
        </div>
      )}

      <div className="shrink-0 pb-6">
        <CalendarHeader
          currentView={view}
          setView={setView}
          onOpenGuide={() => setIsGuideOpen(true)}
        />
      </div>

      <div ref={timelineWrapperRef} className="flex-1 min-h-0">
        <div className="h-full" style={timelineHeight ? { height: timelineHeight } : undefined}>
          <CalendarGrid
            view={view}
            currentDate={currentDate}
            setCurrentDate={setCurrentDate}
            setView={setView}
            events={events}
            onItemClick={handleItemClick}
            onSlotClick={handleSlotClick}
          />
        </div>
      </div>

      <GuideDrawer
        isOpen={isGuideOpen}
        onClose={() => setIsGuideOpen(false)}
      />

      <ItemDetailModal
        item={selectedItem}
        isNew={isNewEvent}
        onClose={handleCloseModal}
        onSave={handleSaveEvent}
        onDelete={handleDeleteEvent}
        projects={projects}
      />
    </div>
  );
}
