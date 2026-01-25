export type ProjectType = 'work' | 'personal';

export interface Flower {
  id: string;
  name: string;
  emoji: string;
  cost: number;
  daysAdded: number;
}

export interface Project {
  id: number;
  name: string;
  active: boolean; // true = active, false = paused
  type: ProjectType;
  color: string;
  progress: number; // 0..100
}

export interface GraveyardProject {
  id: number;
  name: string;
  diedAt: string;     // e.g. "Jan 2026"
  flowers: Flower[];
  type: ProjectType;
  color: string;
  expiryDate: number; // timestamp
  epitaph?: string;
}
