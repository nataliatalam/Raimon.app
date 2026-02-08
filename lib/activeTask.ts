'use client';

export type StoredCoachMessage = {
  title: string;
  message: string;
  next_step: string;
};

export type StoredFocusTask = {
  id: string;
  title: string;
  desc?: string;
  project?: string;
  projectId?: string;
  durationMinutes?: number;
  duration?: string;
  startedAt?: string;
  coach?: StoredCoachMessage | null;
};

const STORAGE_KEY = 'raimon_active_task';

function isBrowser() {
  return typeof window !== 'undefined';
}

export function storeActiveTask(task: StoredFocusTask) {
  if (!isBrowser()) return;
  window.sessionStorage.setItem(STORAGE_KEY, JSON.stringify(task));
}

export function loadActiveTask(): StoredFocusTask | null {
  if (!isBrowser()) return null;
  const raw = window.sessionStorage.getItem(STORAGE_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw) as StoredFocusTask;
  } catch {
    return null;
  }
}

export function clearActiveTask() {
  if (!isBrowser()) return;
  window.sessionStorage.removeItem(STORAGE_KEY);
}
