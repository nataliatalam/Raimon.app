'use client';

import { useEffect, useMemo, useState } from 'react';
import { useRouter } from 'next/navigation';
import FocusChamber from '../../../components/FocusChamber';
import ImStuck from '../../../components/ImStuck';
import { apiFetch, ApiError } from '../../../../lib/api-client';
import { clearActiveTask, loadActiveTask, storeActiveTask, type StoredFocusTask } from '../../../../lib/activeTask';
import type { ApiSuccessResponse } from '../../../../types/api';

type CurrentTaskPayload = {
  current_task: {
    id: string;
    title: string;
    description?: string | null;
    project_id?: string | null;
    project_name?: string | null;
    estimated_duration?: number | null;
  } | null;
  session: {
    id: string;
    start_time: string;
  } | null;
};

export default function FocusPage() {
  const router = useRouter();
  const [task, setTask] = useState<StoredFocusTask | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [stuckOpen, setStuckOpen] = useState(false);

  useEffect(() => {
    const stored = loadActiveTask();
    if (stored) {
      setTask(stored);
      setLoading(false);
    } else {
      fetchCurrentTask();
    }
  }, []);

  async function fetchCurrentTask() {
    setLoading(true);
    setError('');
    try {
      const response = await apiFetch<ApiSuccessResponse<CurrentTaskPayload>>('/api/dashboard/current-task');
      if (response.data.current_task) {
        const mapped: StoredFocusTask = {
          id: response.data.current_task.id,
          title: response.data.current_task.title ?? 'Focus session',
          desc: response.data.current_task.description ?? '',
          project: response.data.current_task.project_name ?? 'General',
          projectId: response.data.current_task.project_id ?? undefined,
          durationMinutes: response.data.current_task.estimated_duration ?? undefined,
          duration: response.data.current_task.estimated_duration
            ? `${response.data.current_task.estimated_duration} min`
            : undefined,
          startedAt: response.data.session?.start_time,
        };
        storeActiveTask(mapped);
        setTask(mapped);
      } else {
        setTask(null);
      }
    } catch (err) {
      if (err instanceof ApiError) setError(err.message);
      else setError('Failed to load current task.');
    } finally {
      setLoading(false);
    }
  }

  async function handleStuck() {
    if (!task?.id) return;
    try {
      await apiFetch(`/api/tasks/${task.id}/intervention`, {
        method: 'POST',
        body: { intervention_type: 'stuck', description: 'User reported being stuck from focus view' },
      });
    } catch {
      // ignore - modal still helps user
    } finally {
      setStuckOpen(true);
    }
  }

  async function handleBreak() {
    if (!task?.id) return;
    try {
      await apiFetch(`/api/tasks/${task.id}/break`, {
        method: 'POST',
        body: { break_type: 'short', reason: 'User tapped Take a break' },
      });
    } catch (err) {
      if (err instanceof ApiError) setError(err.message);
      else setError('Failed to start break.');
    }
  }

  async function handleResume() {
    if (!task?.id) return;
    try {
      await apiFetch(`/api/tasks/${task.id}/start`, { method: 'POST', body: {} });
    } catch (err) {
      if (err instanceof ApiError) setError(err.message);
      else setError('Failed to resume task.');
    }
  }

  async function handleDone() {
    if (!task?.id) {
      setError('No task to complete. Please start a task first.');
      return;
    }
    setError('');
    try {
      await apiFetch(`/api/tasks/${task.id}/complete`, {
        method: 'POST',
        body: { notes: 'Completed from focus chamber' },
      });
      clearActiveTask();
      router.push('/dashboard');
    } catch (err) {
      console.error('Failed to complete task:', err);
      if (err instanceof ApiError) setError(err.message);
      else setError('Failed to complete task. Please try again.');
    }
  }

  const focusTask = useMemo(() => {
    if (!task) return null;
    return {
      title: task.title,
      desc: task.desc ?? '',
      project: task.project ?? 'General',
      duration: task.duration ?? (task.durationMinutes ? `${task.durationMinutes} min` : undefined),
    };
  }, [task]);

  if (loading) {
    return <div style={{ padding: 40, textAlign: 'center' }}>Loading focus session…</div>;
  }

  if (!focusTask) {
    return (
      <div style={{ padding: 40, textAlign: 'center' }}>
        <p>Select a task from the dashboard to start focusing.</p>
      </div>
    );
  }

  return (
    <>
      {error && (
        <div
          style={{
            margin: '16px auto',
            maxWidth: 480,
            padding: '12px 16px',
            borderRadius: 12,
            background: 'rgba(185,28,28,0.08)',
            border: '1px solid rgba(185,28,28,0.25)',
            color: '#7f1d1d',
            textAlign: 'center',
          }}
        >
          {error}
        </div>
      )}
      <FocusChamber
        task={focusTask}
        onStuck={handleStuck}
        onBreak={handleBreak}
        onResume={handleResume}
        onDone={handleDone}
      />
      <ImStuck open={stuckOpen} onClose={() => setStuckOpen(false)} />
    </>
  );
}
