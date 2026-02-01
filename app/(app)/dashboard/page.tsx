'use client';

import { useEffect, useMemo, useState } from 'react';
import { useRouter } from 'next/navigation';
import DailyCheckIn from '../../components/DailyCheckIn';
import TasksPage, { Task } from '../../components/TasksPage';
import type { DaySummaryData } from '../../components/DaySummary';
import { apiFetch, ApiError } from '../../../lib/api-client';
import type { ApiSuccessResponse, DashboardSummaryPayload, DashboardTasksPayload, DashboardTask } from '../../../types/api';
import { storeActiveTask } from '../../../lib/activeTask';
import { useSession } from '../../components/providers/SessionProvider';

export default function DashboardPage() {
  const router = useRouter();
  const { session, status } = useSession();
  const [stage, setStage] = useState<'checkin' | 'tasks'>('checkin');
  const [tasks, setTasks] = useState<Task[]>([]);
  const [tasksLoading, setTasksLoading] = useState(false);
  const [tasksError, setTasksError] = useState('');
  const [summaryData, setSummaryData] = useState<DaySummaryData | undefined>(undefined);
  const [streakCount, setStreakCount] = useState(0);

  useEffect(() => {
    if (typeof window === 'undefined') return;
    const checkedIn = window.sessionStorage.getItem('raimon_checked_in');
    if (checkedIn === 'true') {
      setStage('tasks');
    }
  }, []);

  useEffect(() => {
    if (status !== 'ready' || !session.accessToken) return;
    fetchStreakData();
  }, [status, session.accessToken]);

  async function fetchStreakData() {
    try {
      const response = await apiFetch<ApiSuccessResponse<DashboardSummaryPayload>>('/api/dashboard/summary');
      setStreakCount(response.data.streaks?.daily_check_in ?? 0);
    } catch {
      // Silently fail - streak is non-critical
    }
  }

  useEffect(() => {
    if (stage !== 'tasks' || status !== 'ready' || !session.accessToken) return;
    fetchTasks();
  }, [stage, status, session.accessToken]);

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

  function handleCheckInComplete() {
    if (typeof window !== 'undefined') {
      window.sessionStorage.setItem('raimon_checked_in', 'true');
    }
    setStage('tasks');
  }

  async function handleStartTask(task: Task) {
    if (!task.id) return;
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

  return stage === 'checkin' ? (
    <DailyCheckIn onComplete={handleCheckInComplete} userName={userName} streakCount={streakCount} />
  ) : (
    <TasksPage
      tasks={tasks}
      loading={tasksLoading}
      errorMessage={tasksError}
      summaryData={summaryData}
      userName={session.user?.name ?? undefined}
      onDo={handleStartTask}
      onFinish={handleFinishDay}
    />
  );
}

