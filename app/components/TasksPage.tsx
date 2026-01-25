'use client';

import React, { useMemo, useState } from 'react';
import styles from './TasksPage.module.css';
import DaySummary, { DaySummaryData, Thought } from './DaySummary';

export type Task = {
  title: string; // use "\n" for line breaks
  desc: string;
  project: string;
  duration: string; // e.g. "25 min"
};

type Props = {
  tasks?: Task[];
  summaryData?: DaySummaryData;
  userName?: string;

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
};

export const DEFAULT_TASKS: Task[] = [
  {
    title: 'Review marketing\nbudget proposal',
    desc: "Go through the Q1 marketing budget spreadsheet and add comments for tomorrow’s meeting.",
    project: 'Q1 Planning',
    duration: '25 min',
  },
  {
    title: 'Update client\npresentation',
    desc: "Add the new metrics slides and update the timeline section before Friday’s call.",
    project: 'Client Work',
    duration: '40 min',
  },
  {
    title: 'Write weekly\nreport summary',
    desc: "Compile this week’s highlights and blockers for the team standup.",
    project: 'Team Updates',
    duration: '15 min',
  },
];

export default function TasksPage({
  tasks = DEFAULT_TASKS,
  summaryData,
  userName,
  onDo,
  onFinish,
  onStartTask,
  onFinishDay,
  onCreateProject,
  onAddToExisting,
  onSaveThought,
  onDiscardThought,
}: Props) {
  const [idx, setIdx] = useState(0);
  const [finished, setFinished] = useState(false);

  const safeTasks = tasks.length ? tasks : DEFAULT_TASKS;

  const task = useMemo(() => safeTasks[idx % safeTasks.length], [safeTasks, idx]);

  const doCb = onDo ?? onStartTask;
  const finishCb = onFinish ?? onFinishDay;

  function handleSkip() {
    setIdx((v) => v + 1);
  }

  function handleDo() {
    if (doCb) doCb(task);
    else alert(`Starting: ${task.title.replaceAll('\n', ' ')}`);
  }

  function handleFinish() {
    if (finished) return;
    setFinished(true);
    finishCb?.();
  }

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

  return (
    <div className={styles.page}>
      <header className={styles.header}>
        <div className={styles.headerLeft}>
          <span className={styles.pageLabel}>Up next</span>
          <h1 className={styles.pageTitle}>Your Tasks</h1>
        </div>

        <button
          className={[styles.finishBtn, finished ? styles.finishBtnDone : ''].join(' ')}
          onClick={handleFinish}
          type="button"
        >
          {finished ? 'Done for today!' : 'Finish for today'}
          <span className={styles.finishArrow}>→</span>
        </button>
      </header>

      <main className={styles.content}>
        <div className={styles.taskContainer}>
          <div className={styles.projectPill}>
            <span className={styles.projectDot} />
            <span className={styles.projectName}>{task.project}</span>
          </div>

          <h2 className={styles.taskTitle}>{task.title}</h2>

          <p className={styles.taskDesc}>{task.desc}</p>

          <div className={styles.taskMeta}>
            <div className={styles.metaPill}>
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <span>{task.duration}</span>
            </div>
          </div>

          <div className={styles.actions}>
            <button className={styles.doBtn} onClick={handleDo} type="button">
              <span>Do it</span>
              <span className={styles.arrowCircle} aria-hidden="true">
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M14 5l7 7m0 0l-7 7m7-7H3" />
                </svg>
              </span>
            </button>

            <button className={styles.skipBtn} onClick={handleSkip} type="button">
              Skip this task
            </button>
          </div>
        </div>
      </main>
    </div>
  );
}
