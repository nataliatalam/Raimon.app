'use client';

import type { Flower } from '../app/components/projects/types';
import { apiFetch } from './api-client';
import type { ApiSuccessResponse, GraveyardMetaPayload } from '../types/api';

export type GraveyardMeta = {
  flowers: Flower[];
  epitaph?: string;
  expiryDate: number;
};

const META_KEY = 'raimon_graveyard_meta';

function isBrowser() {
  return typeof window !== 'undefined';
}

function readMeta(): Record<string, GraveyardMeta> {
  if (!isBrowser()) return {};
  try {
    const raw = window.localStorage.getItem(META_KEY);
    if (!raw) return {};
    return JSON.parse(raw) as Record<string, GraveyardMeta>;
  } catch {
    return {};
  }
}

function writeMeta(meta: Record<string, GraveyardMeta>) {
  if (!isBrowser()) return;
  window.localStorage.setItem(META_KEY, JSON.stringify(meta));
}

export function loadAllMeta() {
  return readMeta();
}

export function getProjectMeta(projectId: string): GraveyardMeta | null {
  const meta = readMeta();
  return meta[projectId] ?? null;
}

export function saveProjectMeta(projectId: string, data: GraveyardMeta) {
  const meta = readMeta();
  meta[projectId] = data;
  writeMeta(meta);
}

export function deleteProjectMeta(projectId: string) {
  const meta = readMeta();
  if (meta[projectId]) {
    delete meta[projectId];
    writeMeta(meta);
  }
}

// Backend sync functions

export async function fetchAllGraveyardMeta(): Promise<Record<string, GraveyardMeta>> {
  try {
    const response = await apiFetch<ApiSuccessResponse<{ graveyard: GraveyardMetaPayload[] }>>('/api/users/graveyard');
    const result: Record<string, GraveyardMeta> = {};
    for (const item of response.data.graveyard) {
      result[item.project_id] = {
        flowers: item.flowers.map((f) => ({
          id: f.id,
          name: f.name,
          emoji: f.emoji,
          cost: f.cost,
          daysAdded: f.days_added,
        })),
        epitaph: item.epitaph,
        expiryDate: new Date(item.expiry_date).getTime(),
      };
    }
    // Merge with local and save
    const local = readMeta();
    const merged = { ...local, ...result };
    writeMeta(merged);
    return merged;
  } catch {
    return readMeta();
  }
}

export async function syncGraveyardMeta(projectId: string, data: GraveyardMeta): Promise<void> {
  saveProjectMeta(projectId, data);
  try {
    await apiFetch(`/api/users/graveyard/${projectId}`, {
      method: 'PUT',
      body: {
        flowers: data.flowers.map((f) => ({
          id: f.id,
          name: f.name,
          emoji: f.emoji,
          cost: f.cost,
          days_added: f.daysAdded,
        })),
        epitaph: data.epitaph,
        expiry_date: new Date(data.expiryDate).toISOString(),
      },
    });
  } catch {
    // Silently fail - localStorage is the source of truth
  }
}

export async function deleteGraveyardMetaSync(projectId: string): Promise<void> {
  deleteProjectMeta(projectId);
  try {
    await apiFetch(`/api/users/graveyard/${projectId}`, { method: 'DELETE' });
  } catch {
    // Silently fail
  }
}
