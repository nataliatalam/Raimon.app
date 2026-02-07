'use client';

import React, { useMemo, useState, useEffect } from 'react';
import styles from './TasksPage.module.css';
import DaySummary, { DaySummaryData, Thought } from './DaySummary';
import ProjectFilter from './ProjectFilter';

export type Task = {
  id?: string;
  title: string; // use "\n" for line breaks
  desc: string;
  project: string;
  duration?: string; // e.g. "25 min"
  durationMinutes?: number;
  projectId?: string;
};

type Props = {
  tasks?: Task[];
  summaryData?: DaySummaryData;
  userName?: string;
  loading?: boolean;
  errorMessage?: string;
  emptyMessage?: string;

  /** Preferred prop names */
  onDo?: (task: Task) => void;
  onFinish?: () => void;

  /** Backwards-compatible aliases (so you don't get TS errors if you used these) */
  onStartTask?: (task: Task) => void;
  onFinishDay?: () => void;

  /** Day summary callbacks */
  onCreateProject?: (thought: Thought) => void;
  onAddToExisting?: (thought: Thought) => void;
  onSaveThought?: (thought: Thought) => void;
  onDiscardThought?: (thought: Thought) => void;
  selectedProjects?: string[];
  onSelectedProjectsChange?: (projects: string[]) => void;
};

export const DEFAULT_TASKS: Task[] = [
  {
    title: 'Email Bob',
    desc: "Just a quick follow up.",
    project: 'Admin',
    duration: '5 min',
  },
  {
    title: 'Finalize the Q4 Marketing Strategy Report',
    desc: "Make sure all stakeholders have signed off.",
    project: 'Planning',
    duration: '45 min',
  },
  {
    title: '2',
    desc: "Quick check.",
    project: 'test',
    duration: '2 min',
  },
];

export default function TasksPage({
  tasks = [],
  summaryData,
  userName,
  loading = false,
  errorMessage,
  emptyMessage = "You're all caught up for today.",
  onDo,
  onFinish,
  onStartTask,
  onFinishDay,
  onCreateProject,
  onAddToExisting,
  onSaveThought,
  onDiscardThought,
  selectedProjects: controlledSelectedProjects,
  onSelectedProjectsChange,
}: Props) {
  const [idx, setIdx] = useState(0);
  const [finished, setFinished] = useState(false);
  const [isTransitioning, setIsTransitioning] = useState(false);

  const [internalSelectedProjects, setInternalSelectedProjects] = useState<string[]>([]);
  const selectedProjects = controlledSelectedProjects ?? internalSelectedProjects;

  const setSelectedProjects = (projects: string[]) => {
    if (onSelectedProjectsChange) {
      onSelectedProjectsChange(projects);
    } else {
      setInternalSelectedProjects(projects);
    }
  };

  // Filter Logic
  const filteredTasks = useMemo(() => {
    if (selectedProjects.length === 0) return tasks;
    return tasks.filter(t => selectedProjects.includes(t.project));
  }, [tasks, selectedProjects]);

  const task = useMemo(() => (filteredTasks.length ? filteredTasks[idx % filteredTasks.length] : null), [filteredTasks, idx]);

  // Reset index if filtered list shrinks below current index to avoid jumping too wildly
  useEffect(() => {
    setIdx(0);
  }, [selectedProjects]);

  const doCb = onDo ?? onStartTask;
  const finishCb = onFinish ?? onFinishDay;

  function handleSkip() {
    setIsTransitioning(true);
    setTimeout(() => {
      setIdx((v) => v + 1);
      setIsTransitioning(false);
    }, 400);
  }

  function handleDo() {
    if (!task) return;
    if (doCb) doCb(task);
    else alert(`Starting: ${task.title.replace(/\n/g, ' ')}`);
  }

  function handleFinish() {
    if (finished) return;
    setFinished(true);
    finishCb?.();
  }

  // Dynamic title sizing based on content length
  const getTitleClass = (text: string) => {
    const words = text.split(/\s+/).length;
    const chars = text.length;
    if (chars <= 10 && words <= 2) return styles.titleXL;
    if (chars <= 30 && words <= 5) return styles.titleL;
    return styles.titleM;
  };

  if (finished) {
    return (
      <DaySummary
        data={summaryData}
        userName={userName}
        onCreateProject={onCreateProject}
        onAddToExisting={onAddToExisting}
        onSaveThought={onSaveThought}
        onDiscardThought={onDiscardThought}
      />
    );
  }

  if (loading) {
    return (
      <div className={styles.page}>
        <div className={styles.loadingState}>Loading your tasks...</div>
      </div>
    );
  }

  return (
    <div className={styles.page}>
      {/* Atmospheric Blobs */}
      <div className={styles.blobOrange}></div>
      <div className={styles.blobPurple}></div>
      <div className={styles.blobBlue}></div>

      {/* Grain Overlay */}
      <div className={styles.grainOverlay}></div>

      {/* Header */}
      <header className={styles.header}>
        <div className={styles.headerLeft}>
          <span className={styles.filterLabel}>Tasks from</span>
          <ProjectFilter
            allTasks={tasks}
            selectedProjects={selectedProjects}
            onChange={setSelectedProjects}
          />
        </div>

        {errorMessage && <div className={styles.errorBanner}>{errorMessage}</div>}

        <button
          className={`${styles.finishBtn} ${finished ? styles.finishBtnDone : ''}`}
          onClick={handleFinish}
          type="button"
        >
          <span>Done for today</span>
          <svg
            xmlns="http://www.w3.org/2000/svg"
            width="16"
            height="16"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2.5"
            strokeLinecap="round"
            strokeLinejoin="round"
            className={styles.finishArrow}
          >
            <path d="M5 12h14M12 5l7 7-7 7"/>
          </svg>
        </button>
      </header>

      {/* Content Area */}
      <main className={styles.content}>
        {!task ? (
          <div className={styles.emptyState}>
            <div className={styles.emptyEmoji}>☀️</div>
            <h3 className={styles.emptyTitle}>Day complete.</h3>
            <p className={styles.emptyText}>
              {filteredTasks.length === 0 && tasks.length > 0
                ? "No tasks match your current project filter."
                : emptyMessage}
            </p>
            {(filteredTasks.length === 0 && tasks.length > 0) && (
              <button
                onClick={() => setSelectedProjects([])}
                className={styles.resetBtn}
              >
                Reset Focus
              </button>
            )}
          </div>
        ) : (
          <div className={`${styles.taskGrid} ${isTransitioning ? styles.taskGridTransitioning : ''}`}>
            {/* Left Column: Task Details */}
            <div className={styles.taskDetails}>
              {/* Project Pill (Top) */}
              <div className={styles.projectPill}>
                <span className={styles.projectName}>{task.project}</span>
              </div>

              {/* Title */}
              <h2 className={`${styles.taskTitle} ${getTitleClass(task.title)}`}>{task.title}</h2>

              {/* Description */}
              <p className={styles.taskDesc}>{task.desc || "Focus on your next priority."}</p>

              {/* Duration (Bottom) */}
              {task.duration && (
                <div className={styles.durationDisplay}>
                  <svg xmlns="http://www.w3.org/2000/svg" className={styles.clockIcon} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="3.5">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <span>{task.duration}</span>
                </div>
              )}
            </div>

            {/* Divider (Visible on Desktop) */}
            <div className={styles.divider} />

            {/* Right Column: Actions */}
            <div className={styles.actionsColumn}>
              <div className={styles.doBtnWrapper}>
                <div className={styles.doBtnGlow}></div>
                <button
                  className={styles.doBtn}
                  onClick={handleDo}
                  type="button"
                >
                  <span>Do</span>
                  <span className={styles.arrowCircle}>
                    <svg xmlns="http://www.w3.org/2000/svg" className={styles.arrowIcon} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="4">
                      <path strokeLinecap="round" strokeLinejoin="round" d="M14 5l7 7m0 0l-7 7m7-7H3" />
                    </svg>
                  </span>
                </button>
              </div>

              <button
                className={styles.skipBtn}
                onClick={handleSkip}
                type="button"
              >
                <span>Skip Task</span>
                <div className={styles.skipUnderline}></div>
              </button>
            </div>
          </div>
        )}
      </main>

      {/* Progress Footer */}
      {filteredTasks.length > 0 && (
        <footer className={styles.progressFooter}>
          <div className={styles.progressDots}>
            {filteredTasks.map((_, i) => (
              <button
                key={i}
                onClick={() => setIdx(i)}
                className={`${styles.progressDot} ${i === (idx % filteredTasks.length) ? styles.progressDotActive : ''}`}
                aria-label={`Switch to task ${i + 1}`}
              />
            ))}
          </div>
        </footer>
      )}
    </div>
  );
}
