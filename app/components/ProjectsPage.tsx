'use client';

import { useEffect, useMemo, useState } from 'react';
import ProjectCard from './projects/components/ProjectCard';
import Graveyard from './projects/components/Graveyard';
import type { Project, GraveyardProject, Flower, ProjectStatus } from './projects/types';
import styles from './projects/ProjectsPage.module.css';
import { useSession } from './providers/SessionProvider';
import { apiFetch, ApiError } from '../../lib/api-client';
import type { ApiSuccessResponse, ProjectApiRecord } from '../../types/api';
import {
  deleteProjectMeta,
  deleteGraveyardMetaSync,
  fetchAllGraveyardMeta,
  loadAllMeta,
  saveProjectMeta,
  syncGraveyardMeta,
  type GraveyardMeta,
} from '../../lib/graveyardMeta';
import { earnFlowerPoints, getFlowerPoints, spendFlowerPoints } from '../../lib/flowerPoints';

const DAY_MS = 24 * 60 * 60 * 1000;

function clampProgress(value?: number | null) {
  if (typeof value !== 'number' || Number.isNaN(value)) return 0;
  return Math.max(0, Math.min(100, value));
}

function mapProject(record: ProjectApiRecord): Project {
  return {
    id: record.id,
    name: record.name,
    status: record.status ?? 'active',
    type: record.icon === 'personal' ? 'personal' : 'work',
    color: record.color ?? '#F97316',
    progress: clampProgress(record.progress ?? 0),
    description: record.description ?? null,
    archivedAt: record.archived_at ?? undefined,
  };
}

function defaultMeta(project: Project, now?: number): GraveyardMeta {
  const currentTime = now ?? Date.now();
  const archivedTime = project.archivedAt ? new Date(project.archivedAt).getTime() : currentTime;
  return {
    flowers: [],
    expiryDate: archivedTime + 30 * DAY_MS,
  };
}

export default function ProjectsPage() {
  const { session, status } = useSession();
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [pendingMap, setPendingMap] = useState<Record<string, boolean>>({});
  const [flowerPoints, setFlowerPoints] = useState(30);
  const [graveyardMeta, setGraveyardMeta] = useState<Record<string, GraveyardMeta>>({});
  const [clientNow, setClientNow] = useState<number | null>(null);

  useEffect(() => {
    // Set client time to avoid hydration mismatch
    setClientNow(Date.now());
    setGraveyardMeta(loadAllMeta());
    getFlowerPoints().then(setFlowerPoints);
    fetchAllGraveyardMeta().then(setGraveyardMeta);
  }, []);

  useEffect(() => {
    if (status !== 'ready' || !session.accessToken) return;
    fetchProjects();
  }, [status, session.accessToken]);

  function markPending(id: string, pending: boolean) {
    setPendingMap((prev) => ({ ...prev, [id]: pending }));
  }

  function updateMeta(id: string, updater: (prev: GraveyardMeta) => GraveyardMeta) {
    const now = Date.now(); // Safe here - only called from event handlers
    setGraveyardMeta((prev) => {
      const next = { ...prev };
      const updated = updater(prev[id] ?? { flowers: [], expiryDate: now + 30 * DAY_MS });
      next[id] = updated;
      saveProjectMeta(id, updated);
      syncGraveyardMeta(id, updated);
      return next;
    });
  }

  async function fetchProjects() {
    setLoading(true);
    setError('');
    try {
      const response = await apiFetch<ApiSuccessResponse<{ projects: ProjectApiRecord[] }>>('/api/projects?include_archived=true');
      setProjects(response.data.projects.map(mapProject));
    } catch (err) {
      if (err instanceof ApiError) setError(err.message);
      else setError('Failed to load projects');
    } finally {
      setLoading(false);
    }
  }

  async function archiveProject(project: Project) {
    markPending(project.id, true);
    try {
      await apiFetch(`/api/projects/${project.id}/archive`, { method: 'POST' });
      updateMeta(project.id, () => defaultMeta(project));
      const newBalance = await earnFlowerPoints(2, 'archive_project', project.id);
      setFlowerPoints(newBalance);
      await fetchProjects();
    } catch (err) {
      if (err instanceof ApiError) setError(err.message);
      else setError('Failed to archive project');
    } finally {
      markPending(project.id, false);
    }
  }

  async function restoreProject(projectId: string) {
    markPending(projectId, true);
    try {
      await apiFetch(`/api/projects/${projectId}/restore`, { method: 'POST' });
      deleteProjectMeta(projectId);
      await deleteGraveyardMetaSync(projectId);
      setGraveyardMeta((prev) => {
        const next = { ...prev };
        delete next[projectId];
        return next;
      });
      await fetchProjects();
    } catch (err) {
      if (err instanceof ApiError) setError(err.message);
      else setError('Failed to restore project');
    } finally {
      markPending(projectId, false);
    }
  }

  async function handleToggleStatus(projectId: string) {
    const project = projects.find((p) => p.id === projectId);
    if (!project) return;
    if (project.status === 'active') {
      await archiveProject(project);
    } else {
      await restoreProject(projectId);
    }
  }

  async function handleKillProject(projectId: string) {
    const project = projects.find((p) => p.id === projectId);
    if (!project) return;
    await archiveProject(project);
  }

  async function handleResurrect(projectId: string) {
    if (flowerPoints < 25) return;
    await restoreProject(projectId);
    const newBalance = await spendFlowerPoints(25, 'resurrect', projectId);
    setFlowerPoints(newBalance);
  }

  async function handleBuyFlower(projectId: string, flower: Flower) {
    if (flowerPoints < flower.cost) return;
    updateMeta(projectId, (prev) => ({
      flowers: [...(prev.flowers ?? []), flower],
      expiryDate: (prev.expiryDate ?? Date.now()) + flower.daysAdded * DAY_MS,
      epitaph: prev.epitaph,
    }));
    const newBalance = await spendFlowerPoints(flower.cost, 'buy_flower', projectId);
    setFlowerPoints(newBalance);
  }

  async function handleWriteEpitaph(projectId: string, message: string) {
    if (!message.trim()) return;
    const newBalance = await spendFlowerPoints(5, 'write_epitaph', projectId);
    setFlowerPoints(newBalance);
    updateMeta(projectId, (prev) => ({
      ...prev,
      epitaph: message.trim(),
    }));
  }

  const activeProjects = useMemo(() => projects.filter((p) => p.status === 'active' && p.progress < 100), [projects]);
  const pausedProjects = useMemo(() => projects.filter((p) => p.status === 'archived'), [projects]);
  const completedProjects = useMemo(
    () => projects.filter((p) => p.status === 'completed' || p.progress >= 100),
    [projects],
  );

  const graveyardProjects: GraveyardProject[] = useMemo(
    () =>
      pausedProjects.map((project) => {
        const meta = graveyardMeta[project.id] ?? defaultMeta(project, clientNow ?? undefined);
        return {
          id: project.id,
          name: project.name,
          status: project.status,
          type: project.type,
          color: project.color,
          flowers: meta.flowers ?? [],
          expiryDate: meta.expiryDate,
          epitaph: meta.epitaph,
          diedAt: project.archivedAt && clientNow
            ? new Date(project.archivedAt).toLocaleDateString('en-US', { month: 'short', year: 'numeric' })
            : 'Recently',
        };
      }),
    [pausedProjects, graveyardMeta, clientNow],
  );

  return (
    <div className={styles.scroller}>
      <div className={styles.inner}>
        <header className={styles.header}>
          <div>
            <div className={styles.kicker}>Raimon Workspace</div>
            <h1 className={styles.h1}>
              My <span className={styles.h1Accent}>Projects</span>
            </h1>
          </div>

          {error && <div className={styles.errorBanner}>{error}</div>}
        </header>

        {loading ? (
          <div className={styles.loadingState}>Syncing projects…</div>
        ) : (
          <>
            <section className={styles.section}>
              <div className={styles.sectionHead}>
                <h2>Active</h2>
                <span>{activeProjects.length}</span>
              </div>
              <div className={styles.cards}>
                {activeProjects.length === 0 ? (
                  <div className={styles.emptyState}>No active projects yet.</div>
                ) : (
                  activeProjects.map((project) => (
                    <ProjectCard
                      key={project.id}
                      project={project}
                      onToggleStatus={handleToggleStatus}
                      onKill={handleKillProject}
                      pending={pendingMap[project.id]}
                    />
                  ))
                )}
              </div>
            </section>

            <section className={styles.section}>
              <div className={styles.sectionHead}>
                <h2>Paused</h2>
                <span>{pausedProjects.length}</span>
              </div>
              <div className={styles.cards}>
                {pausedProjects.length === 0 ? (
                  <div className={styles.emptyState}>No paused projects.</div>
                ) : (
                  pausedProjects.map((project) => (
                    <ProjectCard
                      key={`paused-${project.id}`}
                      project={project}
                      onToggleStatus={handleToggleStatus}
                      onKill={handleKillProject}
                      pending={pendingMap[project.id]}
                    />
                  ))
                )}
              </div>
            </section>

            <section className={styles.section}>
              <div className={styles.sectionHead}>
                <h2>Beyond</h2>
                <span>{completedProjects.length}</span>
              </div>
              <div className={styles.cards}>
                {completedProjects.length === 0 ? (
                  <div className={styles.emptyState}>Finish a project to celebrate here.</div>
                ) : (
                  completedProjects.map((project) => (
                    <ProjectCard key={`completed-${project.id}`} project={project} isBeyond pending={pendingMap[project.id]} />
                  ))
                )}
              </div>
            </section>

            <Graveyard
              projects={graveyardProjects}
              flowerPoints={flowerPoints}
              onKillProject={handleKillProject}
              onBuyFlower={handleBuyFlower}
              onResurrect={handleResurrect}
              onWriteEpitaph={handleWriteEpitaph}
            />
          </>
        )}
      </div>
    </div>
  );
}
