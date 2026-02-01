'use client';

import { apiFetch } from './api-client';
import type { ApiSuccessResponse, FlowerPointsPayload } from '../types/api';

const LOCAL_KEY = 'raimon_flower_points';
const DEFAULT_BALANCE = 30;

function isBrowser() {
  return typeof window !== 'undefined';
}

function getLocalBalance(): number {
  if (!isBrowser()) return DEFAULT_BALANCE;
  const raw = window.localStorage.getItem(LOCAL_KEY);
  const parsed = raw ? Number(raw) : NaN;
  return Number.isFinite(parsed) && parsed >= 0 ? parsed : DEFAULT_BALANCE;
}

function setLocalBalance(balance: number) {
  if (!isBrowser()) return;
  window.localStorage.setItem(LOCAL_KEY, String(balance));
}

export async function getFlowerPoints(): Promise<number> {
  try {
    const response = await apiFetch<ApiSuccessResponse<FlowerPointsPayload>>('/api/users/flower-points');
    const balance = response.data.balance;
    setLocalBalance(balance);
    return balance;
  } catch {
    return getLocalBalance();
  }
}

export async function earnFlowerPoints(
  amount: number,
  reason: string,
  projectId?: string
): Promise<number> {
  const currentLocal = getLocalBalance();
  const newLocal = currentLocal + amount;
  setLocalBalance(newLocal);

  try {
    const response = await apiFetch<ApiSuccessResponse<FlowerPointsPayload>>('/api/users/flower-points', {
      method: 'POST',
      body: {
        amount,
        type: 'earned',
        reason,
        project_id: projectId,
      },
    });
    const balance = response.data.balance;
    setLocalBalance(balance);
    return balance;
  } catch {
    return newLocal;
  }
}

export async function spendFlowerPoints(
  amount: number,
  reason: string,
  projectId?: string
): Promise<number> {
  const currentLocal = getLocalBalance();
  if (currentLocal < amount) {
    return currentLocal;
  }
  const newLocal = Math.max(0, currentLocal - amount);
  setLocalBalance(newLocal);

  try {
    const response = await apiFetch<ApiSuccessResponse<FlowerPointsPayload>>('/api/users/flower-points', {
      method: 'POST',
      body: {
        amount,
        type: 'spent',
        reason,
        project_id: projectId,
      },
    });
    const balance = response.data.balance;
    setLocalBalance(balance);
    return balance;
  } catch {
    return newLocal;
  }
}
