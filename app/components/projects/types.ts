export type ProjectType = 'work' | 'personal';
export type ProjectStatus = 'active' | 'archived' | 'completed';

export interface Flower {
  id: string;
  name: string;
  emoji: string;
  cost: number;
  daysAdded: number;
}

export interface Project {
  id: string;
  name: string;
  status: ProjectStatus;
  type: ProjectType;
  color?: string;
  progress: number; // 0..100
  description?: string | null;
  archivedAt?: string;
}

export interface GraveyardProject {
  id: string;
  name: string;
  status: ProjectStatus;
  diedAt: string;     // e.g. "Jan 2026"
  flowers: Flower[];
  type: ProjectType;
  color?: string;
  expiryDate: number; // timestamp
  epitaph?: string;
}
