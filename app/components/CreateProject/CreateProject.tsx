'use client';

import React, { useMemo, useRef, useState } from 'react';
import styles from './CreateProject.module.css';
import { addProject, type StoredProject } from '../../../lib/projectsStore';

type Props = {
  onCreated?: (project: StoredProject) => void;
};

const WORK_COLORS = ['#F97316', '#8B5CF6', '#3B82F6', '#EC4899'];
const PERSONAL_COLORS = ['#10B981', '#F59E0B', '#60A5FA', '#A855F7'];

function pickColor(type: 'work' | 'personal') {
  const arr = type === 'work' ? WORK_COLORS : PERSONAL_COLORS;
  return arr[Math.floor(Math.random() * arr.length)];
}

export default function CreateProject({ onCreated }: Props) {
  const [name, setName] = useState('');
  const [type, setType] = useState<'work' | 'personal'>('work');
  const [brief, setBrief] = useState('');
  const [tasks, setTasks] = useState<string[]>(['']);

  const [timeline, setTimeline] = useState<'Today' | 'Week' | 'Month' | 'Long-term'>('Week');
  const [deadlineMonth, setDeadlineMonth] = useState('');
  const [deadlineDay, setDeadlineDay] = useState('');
  const [deadlineYear, setDeadlineYear] = useState('');
  const [why, setWhy] = useState<string[]>([]);
  const [people, setPeople] = useState<'me' | 'others'>('me');
  const [files, setFiles] = useState<string[]>([]);

  const nameInputRef = useRef<HTMLInputElement | null>(null);

  const canCreate = name.trim().length > 0;

  function addTaskRow() {
    setTasks((prev) => [...prev, '']);
  }

  function toggleWhy(label: string) {
    setWhy((prev) => (prev.includes(label) ? prev.filter((x) => x !== label) : [...prev, label]));
  }

  function addFiles(list: FileList | null) {
    if (!list) return;
    const names = Array.from(list).map((f) => f.name);
    setFiles((prev) => [...prev, ...names]);
  }

  function removeFile(nameToRemove: string) {
    setFiles((prev) => prev.filter((n) => n !== nameToRemove));
  }

  function createProject() {
    if (!canCreate) return;

    const cleanTasks = tasks.map((t) => t.trim()).filter(Boolean);

    const project: StoredProject = {
      id: Date.now() + Math.floor(Math.random() * 1000),
      name: name.trim(),
      type,
      color: pickColor(type),
      active: true,
      progress: 0,
      createdAt: Date.now(),
      brief: brief.trim() || undefined,
      tasks: cleanTasks.length ? cleanTasks : undefined,
    };

    addProject(project);
    onCreated?.(project);
  }

  return (
    <div className={styles.page}>
      {/* Hero */}
      <div className={styles.hero}>
        <h1 className={styles.heroTitle}>
          Let&apos;s build <span className={styles.gradient}>something great.</span>
        </h1>
      </div>

      {/* Section 1: The Basics */}
      <div className={styles.sectionHeader}>
        <div className={styles.sectionNumber}>1</div>
        <span className={styles.sectionTitle}>The Basics</span>
      </div>

      <div className={styles.nameRow}>
        <span className={styles.nameLabel}>I&apos;m working on</span>
        <div className={`${styles.nameInputWrapper} ${!canCreate && name.length ? styles.nameInputError : ''}`}>
          <input
            ref={nameInputRef}
            value={name}
            onChange={(e) => setName(e.target.value)}
            className={styles.nameInput}
            placeholder="Project name..."
          />
        </div>
      </div>

      <div className={styles.typeRow}>
        <span className={styles.typeLabel}>This is a</span>
        <div className={styles.typeToggle}>
          <button
            type="button"
            className={`${styles.typeBtn} ${type === 'work' ? styles.selected : ''}`}
            onClick={() => setType('work')}
          >
            Work
          </button>
          <button
            type="button"
            className={`${styles.typeBtn} ${type === 'personal' ? styles.selected : ''}`}
            onClick={() => setType('personal')}
          >
            Personal
          </button>
        </div>
        <span className={styles.typeLabel}>project</span>
      </div>

      <div className={styles.fieldGroup}>
        <label className={styles.fieldLabel}>Brief (optional)</label>
        <textarea
          className={styles.textInput}
          rows={2}
          value={brief}
          onChange={(e) => setBrief(e.target.value)}
          placeholder="What's this about? What does success look like?"
        />
      </div>

      <div className={styles.fieldGroup}>
        <label className={styles.fieldLabel}>Tasks in mind? (optional)</label>
        <div className={styles.tasksList}>
          {tasks.map((t, idx) => (
            <div key={idx} className={styles.taskRow}>
              <div className={styles.taskCheck} />
              <input
                className={styles.taskInput}
                value={t}
                onChange={(e) => {
                  const v = e.target.value;
                  setTasks((prev) => prev.map((x, i) => (i === idx ? v : x)));
                }}
                placeholder={idx === 0 ? 'First thing to do...' : 'Next task...'}
              />
            </div>
          ))}
          <button type="button" className={styles.addTaskBtn} onClick={addTaskRow}>
            <span className={styles.plus}>＋</span>
            Add another
          </button>
        </div>
      </div>

      {/* Section 2: Add Details */}
      <div className={styles.sectionHeader}>
        <div className={styles.sectionNumber}>2</div>
        <span className={styles.sectionTitle}>Add Details</span>
      </div>

      <div className={styles.detailsList}>
        <div className={styles.detailRow}>
          <span className={styles.label}>Timeline</span>
          <div className={styles.timelineOptions}>
            {(['Today', 'Week', 'Month', 'Long-term'] as const).map((t) => (
              <button
                key={t}
                type="button"
                className={`${styles.timelineBtn} ${timeline === t ? styles.selectedDark : ''}`}
                onClick={() => setTimeline(t)}
              >
                {t}
              </button>
            ))}
          </div>
          <div className={styles.deadlineWrapper}>
            <span className={styles.deadlineLabel}>Deadline (optional)</span>
            <div className={styles.deadlineRow}>
              <select
                className={styles.deadlineSelect}
                value={deadlineMonth}
                onChange={(e) => setDeadlineMonth(e.target.value)}
              >
                <option value="">Month</option>
                {['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'].map((m, i) => (
                  <option key={m} value={String(i + 1).padStart(2, '0')}>{m}</option>
                ))}
              </select>
              <select
                className={styles.deadlineSelect}
                value={deadlineDay}
                onChange={(e) => setDeadlineDay(e.target.value)}
              >
                <option value="">Day</option>
                {Array.from({ length: 31 }, (_, i) => i + 1).map((d) => (
                  <option key={d} value={String(d).padStart(2, '0')}>{d}</option>
                ))}
              </select>
              <select
                className={styles.deadlineSelect}
                value={deadlineYear}
                onChange={(e) => setDeadlineYear(e.target.value)}
              >
                <option value="">Year</option>
                {Array.from({ length: 11 }, (_, i) => 2026 + i).map((y) => (
                  <option key={y} value={String(y)}>{y}</option>
                ))}
              </select>
              {(deadlineMonth || deadlineDay || deadlineYear) && (
                <button
                  type="button"
                  className={styles.deadlineClear}
                  onClick={() => {
                    setDeadlineMonth('');
                    setDeadlineDay('');
                    setDeadlineYear('');
                  }}
                  aria-label="Clear deadline"
                >
                  ✕
                </button>
              )}
            </div>
          </div>
        </div>

        <div className={styles.detailRow}>
          <span className={styles.label}>Why it matters</span>
          <div className={styles.pillsRow}>
            {['Deadline', 'Money', 'Health', 'Growth', 'Relationships'].map((p) => (
              <button
                key={p}
                type="button"
                className={`${styles.pill} ${why.includes(p) ? styles.selectedDark : ''}`}
                onClick={() => toggleWhy(p)}
              >
                {p}
              </button>
            ))}
          </div>
        </div>

        <div className={styles.detailRow}>
          <span className={styles.label}>Who&apos;s involved?</span>
          <div className={styles.pillsRow}>
            <button
              type="button"
              className={`${styles.pill} ${people === 'me' ? styles.selectedDark : ''}`}
              onClick={() => setPeople('me')}
            >
              Just me
            </button>
            <button
              type="button"
              className={`${styles.pill} ${people === 'others' ? styles.selectedDark : ''}`}
              onClick={() => setPeople('others')}
            >
              Others too
            </button>
          </div>
        </div>

        <div className={styles.detailRow}>
          <span className={styles.label}>Links &amp; Docs (optional)</span>
          <label
            className={styles.dropZone}
            onDragOver={(e) => e.preventDefault()}
            onDrop={(e) => {
              e.preventDefault();
              addFiles(e.dataTransfer.files);
            }}
          >
            <input
              type="file"
              multiple
              className={styles.fileInput}
              onChange={(e) => addFiles(e.target.files)}
            />
            <div className={styles.dropIcon}>⤒</div>
            <p>
              Drop files here or <span>browse</span>
            </p>
          </label>
          {files.length > 0 && (
            <div className={styles.attachedFiles}>
              {files.map((f) => (
                <div key={f} className={styles.filePill}>
                  {f}
                  <button type="button" onClick={() => removeFile(f)} aria-label="Remove">
                    ✕
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      <div className={styles.footer}>
        <button type="button" className={styles.btnPrimary} onClick={createProject}>
          Create Project
        </button>
      </div>
    </div>
  );
}
