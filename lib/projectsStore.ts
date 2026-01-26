export type StoredProject = {
  id: number;
  name: string;
  type: 'work' | 'personal';
  color: string;
  active: boolean;
  progress: number;
  createdAt?: number;

  // opcional para demo (no rompe nada si no lo usas)
  brief?: string;
  tasks?: string[];
};

const KEY = 'raimon_projects_v1';

function safeParse<T>(raw: string | null): T | null {
  if (!raw) return null;
  try {
    return JSON.parse(raw) as T;
  } catch {
    return null;
  }
}

export function loadProjects(): StoredProject[] {
  if (typeof window === 'undefined') return [];
  const data = safeParse<StoredProject[]>(localStorage.getItem(KEY));
  return Array.isArray(data) ? data : [];
}

export function saveProjects(projects: StoredProject[]) {
  if (typeof window === 'undefined') return;
  localStorage.setItem(KEY, JSON.stringify(projects));
}

export function addProject(p: StoredProject) {
  const prev = loadProjects();
  const next = [p, ...prev];
  saveProjects(next);
  return next;
}

export function ensureSeedProjects(seed: StoredProject[]) {
  const existing = loadProjects();
  if (existing.length) return existing;
  saveProjects(seed);
  return seed;
}
