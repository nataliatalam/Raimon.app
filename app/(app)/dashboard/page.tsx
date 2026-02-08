'use client';

import { useEffect, useMemo, useState } from 'react';
import { useRouter } from 'next/navigation';
import { ArrowRight } from 'lucide-react';
import DailyCheckIn from '../../components/DailyCheckIn';
import TasksPage, { Task } from '../../components/TasksPage';
import type { DaySummaryData } from '../../components/DaySummary';
import HomeDashboard from '../../components/HomeDashboard';
import ProjectFilter from '../../components/ProjectFilter';
import type { CalendarEvent } from '../../components/calendar/types';
import { apiFetch, ApiError } from '../../../lib/api-client';
import type {
  ApiSuccessResponse,
  DashboardSummaryPayload,
  DashboardTasksPayload,
  DashboardTask,
  ProjectApiRecord,
} from '../../../types/api';
import { storeActiveTask } from '../../../lib/activeTask';
import { useSession } from '../../components/providers/SessionProvider';

type AgentCoachMessage = {
  title: string;
  message: string;
  next_step: string;
};

type AgentActiveDoPayload = {
  task?: {
    id?: string;
    title?: string;
    description?: string | null;
    project_id?: string | null;
    project_name?: string | null;
    estimated_duration?: number | null;
  };
  reason_codes?: string[];
  alt_task_ids?: string[];
  selected_at?: string;
};

type AgentNextDoResponse = {
  success: boolean;
  data?: {
    active_do?: AgentActiveDoPayload;
    coach_message?: AgentCoachMessage;
  };
  error?: string;
};

type SelectionConstraintPayload = {
  max_minutes: number;
  mode: 'quick' | 'balanced' | 'focus';
  current_energy: number;
};

// API response type (snake_case from backend)
type ApiCalendarEvent = {
  id: string;
  title: string;
  start_time: string;
  end_time: string;
  event_type: string;
  location?: string;
};
const EVENTS_STORAGE_KEY = 'raimon_calendar_events';
const DEFAULT_MAX_MINUTES = 120;

function loadStoredEvents(): CalendarEvent[] {
  if (typeof window === 'undefined') return [];
  try {
    const payload = window.localStorage.getItem(EVENTS_STORAGE_KEY);
    if (!payload) return [];
    const parsed = JSON.parse(payload) as Array<Record<string, unknown>>;
    return parsed.map((event) => ({
      id: String(event.id ?? `evt_${Math.random()}`),
      title: String(event.title ?? 'Untitled'),
      startTime: new Date(String(event.startTime)),
      endTime: new Date(String(event.endTime)),
      project: typeof event.project === 'string' ? event.project : undefined,
      projectId: typeof event.projectId === 'string' ? event.projectId : undefined,
      category: (event.category as CalendarEvent['category']) ?? 'OTHER',
      source: (event.source as CalendarEvent['source']) ?? 'manual',
      relatedId: typeof event.relatedId === 'string' ? event.relatedId : undefined,
    }));
  } catch {
    return [];
  }
}

function buildDeadlineEvents(records: ProjectApiRecord[]): CalendarEvent[] {
  const results: CalendarEvent[] = [];

  const coerceRange = (value: string | null | undefined) => {
    if (!value) return null;
    const iso = value.includes('T') ? value : `${value}T09:00:00`;
    const start = new Date(iso);
    if (Number.isNaN(start.getTime())) return null;
    const end = new Date(start);
    end.setHours(end.getHours() + 1);
    return { start, end };
  };

  records.forEach((record) => {
    const category: CalendarEvent['category'] = record.icon === 'personal' ? 'PERSONAL' : 'WORK';
    const projectDeadline = record.target_end_date ?? record.deadline ?? null;
    if (projectDeadline) {
      const range = coerceRange(projectDeadline);
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
      const range = coerceRange(task.deadline);
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
}

function deriveModeFromEnergy(energyLevel: number): SelectionConstraintPayload['mode'] {
  if (energyLevel <= 3) return 'quick';
  if (energyLevel >= 8) return 'focus';
  return 'balanced';
}

function buildConstraintsFromEnergy(energyLevel: number | null): SelectionConstraintPayload {
  const normalized = typeof energyLevel === 'number' && energyLevel >= 1 ? energyLevel : 5;
  return {
    max_minutes: DEFAULT_MAX_MINUTES,
    current_energy: normalized,
    mode: deriveModeFromEnergy(normalized),
  };
}

function mapAgentActiveDoToTask(
  activeDo?: AgentActiveDoPayload | null,
  coach?: AgentCoachMessage | null,
): Task | null {
  const rawTask = activeDo?.task;
  if (!rawTask?.id) return null;
  const duration = typeof rawTask.estimated_duration === 'number' ? rawTask.estimated_duration : undefined;

  let desc = rawTask.description ?? 'Raimon thinks this is the best next move right now.';
  if (coach) {
    const guidance = coach.next_step ? `${coach.message} Next: ${coach.next_step}` : coach.message;
    desc = `${coach.title}\n${guidance}`.trim();
  }

  return {
    id: rawTask.id,
    title: rawTask.title ?? 'AI-selected task',
    desc,
    project: rawTask.project_name ?? 'AI Recommendation',
    duration: duration ? `${duration} min` : undefined,
    durationMinutes: duration,
    projectId: rawTask.project_id ?? undefined,
  };
}

export default function DashboardPage() {
  const router = useRouter();
  const { session, status } = useSession();
  const [stage, setStage] = useState<'checkin' | 'home' | 'tasks'>('checkin');
  const [tasks, setTasks] = useState<Task[]>([]);
  const [calendarEvents, setCalendarEvents] = useState<ApiCalendarEvent[]>([]);
  const [tasksLoading, setTasksLoading] = useState(false);
  const [tasksError, setTasksError] = useState('');
  const [summaryData, setSummaryData] = useState<DaySummaryData | undefined>(undefined);
  const [streakCount, setStreakCount] = useState(0);
  const [todayEnergy, setTodayEnergy] = useState<number | null>(null);
  const [agentActiveDo, setAgentActiveDo] = useState<AgentActiveDoPayload | null>(null);
  const [agentCoachMessage, setAgentCoachMessage] = useState<AgentCoachMessage | null>(null);
  const [agentError, setAgentError] = useState('');
  const [selectedProjects, setSelectedProjects] = useState<string[]>([]);
  const [nextEvent, setNextEvent] = useState<CalendarEvent | null>(null);

  useEffect(() => {
    if (typeof window === 'undefined') return;
    if (status !== 'ready' || !session.user?.id) return;

    const today = new Date().toISOString().split('T')[0];
    const storageKey = `raimon_checked_in_${session.user.id}`;
    const checkedInData = window.sessionStorage.getItem(storageKey);

    if (checkedInData === today) {
      setStage('home');
    }
  }, [status, session.user?.id]);

  useEffect(() => {
    if (status !== 'ready' || !session.accessToken) return;
    fetchStreakData();
  }, [status, session.accessToken]);

  async function fetchStreakData() {
    try {
      const response = await apiFetch<ApiSuccessResponse<DashboardSummaryPayload>>('/api/dashboard/summary');
      setStreakCount(response.data.streaks?.daily_check_in ?? 0);
      setTodayEnergy(response.data.today.energy_level ?? null);
    } catch {
      // Non-blocking
    }
  }

  useEffect(() => {
    if (stage !== 'tasks' || status !== 'ready' || !session.accessToken) return;
    fetchTasks();
    fetchCalendarEvents();
    fetchRecommendation();
  }, [stage, status, session.accessToken]);

  useEffect(() => {
    if (stage !== 'home' || status !== 'ready' || !session.accessToken) return;
    let cancelled = false;

    async function loadNextEvent() {
      const manualEvents = loadStoredEvents();
      let projectEvents: CalendarEvent[] = [];
      try {
        const response = await apiFetch<ApiSuccessResponse<{ projects: ProjectApiRecord[] }>>(
          '/api/projects?include_task_deadlines=true'
        );
        projectEvents = buildDeadlineEvents(response.data.projects);
      } catch {
        projectEvents = [];
      }

      const combined = [...manualEvents, ...projectEvents];
      const now = new Date();
      combined.sort((a, b) => a.startTime.getTime() - b.startTime.getTime());
      const todayMatches = combined.filter(
        (event) => event.startTime >= now && event.startTime.toDateString() === now.toDateString()
      );
      if (!cancelled) {
        setNextEvent(todayMatches[0] ?? combined.find((event) => event.startTime >= now) ?? null);
      }
    }

    loadNextEvent();

    return () => {
      cancelled = true;
    };
  }, [stage, status, session.accessToken]);

  async function fetchCalendarEvents() {
    try {
      const response = await apiFetch<{ success: boolean; data: { events: ApiCalendarEvent[] } }>('/api/calendar/today');
      if (response.success && response.data.events) {
        setCalendarEvents(response.data.events);
      }
    } catch {
      // Silently fail - calendar is optional
    }
  }

  async function fetchLatestEnergy(): Promise<number | null> {
    try {
      const response = await apiFetch<ApiSuccessResponse<DashboardSummaryPayload>>('/api/dashboard/summary');
      const energy = response.data.today.energy_level ?? null;
      setTodayEnergy(energy);
      return energy;
    } catch {
      return todayEnergy;
    }
  }

  async function fetchRecommendation(forceEnergyRefresh = false) {
    setAgentError('');
    try {
      let energy = todayEnergy;
      if (forceEnergyRefresh || energy == null) {
        energy = await fetchLatestEnergy();
      }
      const constraints = buildConstraintsFromEnergy(energy);
      const response = await apiFetch<AgentNextDoResponse>('/api/agent-mvp/next-do', {
        method: 'POST',
        body: { constraints },
      });

      if (response.success && response.data) {
        setAgentActiveDo(response.data.active_do ?? null);
        setAgentCoachMessage(response.data.coach_message ?? null);
      } else {
        setAgentActiveDo(null);
        setAgentCoachMessage(null);
        setAgentError(response.error || 'Failed to get AI recommendation.');
      }
    } catch (err) {
      setAgentActiveDo(null);
      setAgentCoachMessage(null);
      if (err instanceof ApiError) setAgentError(err.message);
      else setAgentError('Failed to get AI recommendation.');
    }
  }

  async function fetchTasks() {
    setTasksLoading(true);
    setTasksError('');
    try {
      const response = await apiFetch<ApiSuccessResponse<DashboardTasksPayload>>('/api/dashboard/today-tasks');
      setTasks((response.data.pending ?? []).map(mapTask));
    } catch (err) {
      if (err instanceof ApiError) setTasksError(err.message);
      else setTasksError('Failed to load today’s tasks.');
    } finally {
      setTasksLoading(false);
    }
  }

  function mapTask(task: DashboardTask): Task {
    return {
      id: task.id,
      title: task.title ?? 'Untitled task',
      desc: task.description ?? 'No description yet.',
      project: task.project_name ?? 'General',
      duration: task.estimated_duration ? `${task.estimated_duration} min` : undefined,
      durationMinutes: task.estimated_duration ?? undefined,
      projectId: task.project_id ?? undefined,
    };
  }

  function mapCalendarEventToTask(event: ApiCalendarEvent): Task {
    const startTime = new Date(event.start_time);
    const endTime = new Date(event.end_time);
    const durationMinutes = Math.round((endTime.getTime() - startTime.getTime()) / 60000);
    const timeStr = startTime.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

    return {
      id: `calendar-${event.id}`,
      title: event.title,
      desc: event.location ? `📍 ${event.location} • ${timeStr}` : `🕐 ${timeStr}`,
      project: '📅 Calendar',
      duration: `${durationMinutes} min`,
      durationMinutes,
    };
  }

  const aiTaskEntry = useMemo(
    () => mapAgentActiveDoToTask(agentActiveDo, agentCoachMessage),
    [agentActiveDo, agentCoachMessage],
  );

  const prioritizedTasks = useMemo(() => {
    if (!aiTaskEntry) return tasks;
    return [aiTaskEntry, ...tasks.filter((task) => task.id !== aiTaskEntry.id)];
  }, [tasks, aiTaskEntry]);

  // Combine tasks with calendar events
  const allTasks = useMemo(() => {
    const calendarTasks = calendarEvents.map(mapCalendarEventToTask);
    // Sort calendar events by time, put them first
    calendarTasks.sort((a, b) => {
      const timeA = a.desc.match(/\d{1,2}:\d{2}/)?.[0] || '';
      const timeB = b.desc.match(/\d{1,2}:\d{2}/)?.[0] || '';
      return timeA.localeCompare(timeB);
    });
    return [...calendarTasks, ...prioritizedTasks];
  }, [prioritizedTasks, calendarEvents]);

  function handleCheckInComplete() {
    if (typeof window !== 'undefined' && session.user?.id) {
      const today = new Date().toISOString().split('T')[0];
      const storageKey = `raimon_checked_in_${session.user.id}`;
      window.sessionStorage.setItem(storageKey, today);
    }
    setStage('home');
  }

  async function handleStartTask(task: Task) {
    if (!task.id) return;

    // Calendar events can't be "started" as tasks
    if (task.id.startsWith('calendar-')) {
      alert(`📅 "${task.title}" is a calendar event scheduled for ${task.desc.replace(/[📍🕐]\s*/g, '')}`);
      return;
    }

    setTasksError('');
    try {
      await apiFetch(`/api/tasks/${task.id}/start`, { method: 'POST', body: {} });
      storeActiveTask({
        id: task.id,
        title: task.title,
        desc: task.desc,
        project: task.project,
        duration: task.duration,
        durationMinutes: task.durationMinutes,
        projectId: task.projectId,
        startedAt: new Date().toISOString(),
      });
      try {
        await apiFetch('/api/agent-mvp/do-action', {
          method: 'POST',
          body: { action: 'start', task_id: task.id },
        });
      } catch (agentErr) {
        console.warn('Failed to notify orchestrator about task start', agentErr);
      }
      router.push('/dashboard/focus');
    } catch (err) {
      if (err instanceof ApiError) setTasksError(err.message);
      else setTasksError('Failed to start task.');
    }
  }

  async function handleFinishDay() {
    try {
      const response = await apiFetch<ApiSuccessResponse<DashboardSummaryPayload>>('/api/dashboard/summary');
      const today = response.data.today;
      const weekData = Array.from({ length: 7 }, (_, index) => {
        if (index === new Date().getDay()) {
          return Math.min(100, today.focus_time);
        }
        return Math.max(10, Math.min(80, today.tasks_completed * 10));
      });
      setSummaryData({
        tasksCompleted: today.tasks_completed,
        focusMinutes: today.focus_time,
        breaks: 0,
        streak: response.data.streaks?.daily_check_in ?? 0,
        baselinePercent: Math.min(100, today.focus_time),
        weekData,
        thoughts: [],
      });
    } catch (err) {
      if (err instanceof ApiError) setTasksError(err.message);
      else setTasksError('Failed to load summary.');
    }
  }

  const userName = useMemo(() => session.user?.name ?? 'there', [session.user?.name]);

  if (stage === 'checkin') {
    return <DailyCheckIn onComplete={handleCheckInComplete} userName={userName} streakCount={streakCount} />;
  }

  if (stage === 'home') {
    const projectFilterControl = (
      <ProjectFilter
        allTasks={tasks}
        selectedProjects={selectedProjects}
        onChange={setSelectedProjects}
        renderTrigger={({ title, onOpen }) => (
          <button
            type="button"
            onClick={onOpen}
            className="bg-white/5 border border-white/10 rounded-full px-8 py-5 flex items-center gap-6 hover:bg-white/10 hover:border-[#FF6B00]/50 transition-all active:scale-95 group/btn"
          >
            <span className="text-2xl lg:text-3xl font-black text-white uppercase tracking-tighter">{title}</span>
            <div className="h-6 w-[1px] bg-white/10" />
            <div className="flex items-center gap-2 text-[#FF6B00]">
              <span className="text-[10px] font-black uppercase tracking-[0.2em]">Change</span>
              <ArrowRight size={16} className="group-hover/btn:translate-x-1 transition-transform" />
            </div>
          </button>
        )}
      />
    );

    return (
      <HomeDashboard
        userName={session.user?.name ?? undefined}
        streakCount={streakCount}
        projectFilterControl={projectFilterControl}
        onStartDoing={() => setStage('tasks')}
        onOpenCalendar={() => router.push('/calendar')}
        nextEvent={nextEvent}
      />
    );
  }

  return (
    <TasksPage
      tasks={allTasks}
      loading={tasksLoading}
      errorMessage={tasksError || agentError}
      summaryData={summaryData}
      userName={session.user?.name ?? undefined}
      onDo={handleStartTask}
      onFinish={handleFinishDay}
      selectedProjects={selectedProjects}
      onSelectedProjectsChange={setSelectedProjects}
    />
  );
}
