'use client';

import { useEffect, useMemo, useState } from 'react';
import { Eye, Pause, Skull } from 'lucide-react';

import ProjectCard from './projects/components/ProjectCard';
import Graveyard from './projects/components/Graveyard';
import type { Project, GraveyardProject, Flower } from './projects/types';
import styles from './projects/ProjectsPage.module.css';

// ✅ FIX: usa ruta relativa (porque "lib/..." no está configurado como alias)
import { ensureSeedProjects, saveProjects, type StoredProject } from '../../lib/projectsStore';

// ✅ Seed: solo se usa si no hay nada aún en localStorage
const SEED_PROJECTS: StoredProject[] = [
  { id: 1, name: 'Q1 Strategy', active: true, type: 'work', color: '#F97316', progress: 25 },
  { id: 2, name: 'Website Redesign', active: true, type: 'work', color: '#8B5CF6', progress: 80 },
  { id: 3, name: 'Learn Jazz', active: false, type: 'personal', color: '#10B981', progress: 10 },
  { id: 5, name: 'Marathon', active: true, type: 'personal', color: '#3B82F6', progress: 45 },
  { id: 6, name: 'App Launch', active: false, type: 'work', color: '#F43F5E', progress: 100 },
  { id: 7, name: 'Photography', active: false, type: 'personal', color: '#F59E0B', progress: 100 },
];

function toUI(p: StoredProject): Project {
  return {
    id: p.id,
    name: p.name,
    active: p.active ?? true,
    type: p.type,
    color: p.color ?? '#F97316',
    progress: typeof p.progress === 'number' ? p.progress : 0,
  };
}

function toStored(p: Project): StoredProject {
  return {
    id: p.id,
    name: p.name,
    active: p.active,
    type: p.type,
    color: p.color,
    progress: p.progress,
  };
}

export default function ProjectsPage() {
  const [flowerPoints, setFlowerPoints] = useState(30);

  const [projects, setProjects] = useState<Project[]>([]);
  const [hydrated, setHydrated] = useState(false);

  const [graveyard, setGraveyard] = useState<GraveyardProject[]>([
    {
      id: 101,
      name: 'Podcast',
      diedAt: 'Jan 2026',
      flowers: [],
      type: 'personal',
      color: '#EC4899',
      expiryDate: Date.now() + 1000 * 60 * 60 * 24 * 5,
    },
  ]);

  // ✅ Load from localStorage (or seed once)
  useEffect(() => {
    const stored = ensureSeedProjects(SEED_PROJECTS);
    setProjects(stored.map(toUI));
    setHydrated(true);
  }, []);

  // ✅ Persist whenever projects change (after first load)
  useEffect(() => {
    if (!hydrated) return;
    saveProjects(projects.map(toStored));
  }, [projects, hydrated]);

  const activeProjects = useMemo(
    () => projects.filter((p) => p.active && p.progress < 100),
    [projects]
  );
  const pausedProjects = useMemo(
    () => projects.filter((p) => !p.active && p.progress < 100),
    [projects]
  );
  const beyondProjects = useMemo(
    () => projects.filter((p) => p.progress === 100),
    [projects]
  );

  function toggleProjectStatus(id: number) {
    setProjects((prev) => prev.map((p) => (p.id === id ? { ...p, active: !p.active } : p)));
  }

  function killProject(id: number) {
    const project = projects.find((p) => p.id === id);
    if (!project) return;

    setGraveyard((prev) => [
      ...prev,
      {
        id: project.id,
        name: project.name,
        diedAt: new Date().toLocaleDateString('en-US', { month: 'short', year: 'numeric' }),
        flowers: [],
        type: project.type,
        color: project.color,
        expiryDate: Date.now() + 1000 * 60 * 60 * 24 * 30,
      },
    ]);

    setProjects((prev) => prev.filter((p) => p.id !== id));
    setFlowerPoints((v) => v + 2);
  }

  function buyFlower(projectId: number, flower: Flower) {
    if (flowerPoints < flower.cost) return;
    setFlowerPoints((v) => v - flower.cost);

    setGraveyard((prev) =>
      prev.map((p) => {
        if (p.id !== projectId) return p;
        return {
          ...p,
          flowers: [...p.flowers, flower],
          expiryDate: p.expiryDate + flower.daysAdded * 24 * 60 * 60 * 1000,
        };
      })
    );
  }

  function writeEpitaph(projectId: number, message: string) {
    const cost = 5;
    if (flowerPoints < cost) return;
    setFlowerPoints((v) => v - cost);

    setGraveyard((prev) => prev.map((p) => (p.id === projectId ? { ...p, epitaph: message } : p)));
  }

  function resurrectProject(id: number) {
    const cost = 25;
    if (flowerPoints < cost) return;

    const graveProject = graveyard.find((p) => p.id === id);
    if (!graveProject) return;

    setFlowerPoints((v) => v - cost);
    setProjects((prev) => [
      ...prev,
      {
        id: graveProject.id,
        name: graveProject.name,
        active: false,
        type: graveProject.type,
        color: graveProject.color,
        progress: 0,
      },
    ]);
    setGraveyard((prev) => prev.filter((p) => p.id !== id));
  }

  function viewProject(id: number) {
    alert(`Opening project ${id} (coming soon)`);
  }

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

          <div className={styles.legend}>
            <div className={styles.legendTitle}>Control Guide</div>

            <div className={styles.legendRow}>
              <span className={styles.legendIcon}>
                <Eye size={14} />
              </span>
              <span>View</span>
            </div>

            <div className={styles.legendRow}>
              <span className={styles.legendIconOrange}>
                <Pause size={14} />
              </span>
              <span>Pause/Resume</span>
            </div>

            <div className={styles.legendRow}>
              <span className={styles.legendIconGray}>
                <Skull size={14} />
              </span>
              <span>Graveyard</span>
            </div>
          </div>
        </header>

        <section className={styles.section}>
          <div className={styles.sectionHead}>
            <h2 className={styles.h2}>Active Flows</h2>
            <div className={styles.rule} />
          </div>

          {activeProjects.length ? (
            <div className={styles.grid3}>
              {activeProjects.map((p) => (
                <ProjectCard
                  key={p.id}
                  project={p}
                  onToggleStatus={toggleProjectStatus}
                  onKill={killProject}
                  onView={viewProject}
                />
              ))}
            </div>
          ) : (
            <div className={styles.empty}>No active flows. Start one or resurrect a dream.</div>
          )}
        </section>

        <section className={styles.sectionMuted}>
          <div className={styles.sectionHead}>
            <h2 className={styles.h2Muted}>Paused</h2>
            <div className={styles.rule} />
          </div>

          {pausedProjects.length ? (
            <div className={styles.grid4}>
              {pausedProjects.map((p) => (
                <ProjectCard
                  key={p.id}
                  project={p}
                  onToggleStatus={toggleProjectStatus}
                  onKill={killProject}
                  onView={viewProject}
                />
              ))}
            </div>
          ) : (
            <div className={styles.miniEmpty}>Nothing on hold.</div>
          )}
        </section>

        {beyondProjects.length > 0 && (
          <section className={styles.section}>
            <div className={styles.sectionHead}>
              <h2 className={styles.h2}>Projects Beyond</h2>
              <div className={styles.rule} />
            </div>

            <p className={styles.desc}>
              These flows are complete. You can view them, but they no longer require your active attention.
            </p>

            <div className={styles.grid4}>
              {beyondProjects.map((p) => (
                <ProjectCard key={p.id} project={p} isBeyond />
              ))}
            </div>
          </section>
        )}

        <Graveyard
          projects={graveyard}
          flowerPoints={flowerPoints}
          onKillProject={killProject}
          onBuyFlower={buyFlower}
          onResurrect={resurrectProject}
          onWriteEpitaph={writeEpitaph}
        />
      </div>
    </div>
  );
}
