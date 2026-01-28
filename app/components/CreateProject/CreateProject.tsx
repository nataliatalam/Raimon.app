'use client';

import React, { useMemo, useRef, useState } from 'react';
import styles from './CreateProject.module.css';
import { apiFetch, ApiError } from '../../../lib/api-client';
import type { ApiSuccessResponse, ProjectApiRecord } from '../../../types/api';

type Props = {
  onCreated?: (projectId: string) => void;
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
  const [files, setFiles] = useState<File[]>([]);
  const [serverError, setServerError] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const nameInputRef = useRef<HTMLInputElement | null>(null);

  const canCreate = name.trim().length > 0 && !isSubmitting;

  function addTaskRow() {
    setTasks((prev) => [...prev, '']);
  }

  function toggleWhy(label: string) {
    setWhy((prev) => (prev.includes(label) ? prev.filter((x) => x !== label) : [...prev, label]));
  }

  function addFiles(list: FileList | null) {
    if (!list) return;
    setFiles((prev) => [...prev, ...Array.from(list)]);
  }

  function removeFile(indexToRemove: number) {
    setFiles((prev) => prev.filter((_, index) => index !== indexToRemove));
  }

  const deadlineIso = useMemo(() => {
    if (!deadlineMonth || !deadlineDay || !deadlineYear) return undefined;
    return `${deadlineYear}-${deadlineMonth}-${deadlineDay}`;
  }, [deadlineMonth, deadlineDay, deadlineYear]);

  async function handleCreate() {
    if (!canCreate) return;
    setServerError('');
    setIsSubmitting(true);
    try {
      const cleanTasks = tasks.map((t) => t.trim()).filter(Boolean);

      const payload: Record<string, unknown> = {
        name: name.trim(),
        description: brief.trim() || undefined,
        priority: type === 'work' ? 2 : 1,
        color: pickColor(type),
        icon: type,
        details: {
          tasks: cleanTasks,
          timeline,
          why,
          people,
        },
      };

      if (deadlineIso) {
        payload.target_end_date = deadlineIso;
        (payload.details as Record<string, unknown>).deadline = deadlineIso;
      }

      const response = await apiFetch<ApiSuccessResponse<{ project: ProjectApiRecord }>>('/api/projects', {
        method: 'POST',
        body: payload,
      });

      const projectId = response.data.project.id;

      if (files.length) {
        const uploadData = new FormData();
        files.forEach((file) => {
          uploadData.append('files', file, file.name);
        });

        try {
          await apiFetch(`/api/projects/${projectId}/files`, {
            method: 'POST',
            body: uploadData,
          });
        } catch (uploadError) {
          console.error('Failed to upload project files', uploadError);
          setServerError('Project created, but some files could not be uploaded.');
        }
      }

      onCreated?.(projectId);
    } catch (err) {
      if (err instanceof ApiError) {
        setServerError(err.message);
      } else {
        setServerError('Failed to create project. Please try again.');
      }
    } finally {
      setIsSubmitting(false);
    }
  }
  return (
    <div className={styles.page}>
      {/* Hero */}
      <div className={styles.hero}>
        <h1 className={styles.heroTitle}>
          Let&apos;s build <span className={styles.gradient}>something great.</span>
        </h1>
      </div>

      {serverError && <div className={styles.errorBanner}>{serverError}</div>}

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
            disabled={isSubmitting}
          >
            Work
          </button>
          <button
            type="button"
            className={`${styles.typeBtn} ${type === 'personal' ? styles.selected : ''}`}
            onClick={() => setType('personal')}
            disabled={isSubmitting}
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
            {(['Today', 'Week', 'Month', 'Long-term'] as const).map((tVal) => (
              <button
                key={tVal}
                type="button"
                className={`${styles.timelineBtn} ${timeline === tVal ? styles.selectedDark : ''}`}
                onClick={() => setTimeline(tVal)}
                disabled={isSubmitting}
              >
                {tVal}
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
                disabled={isSubmitting}
              >
                <option value="">Month</option>
                {['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'].map((m, i) => (
                  <option key={m} value={String(i + 1).padStart(2, '0')}>
                    {m}
                  </option>
                ))}
              </select>
              <select
                className={styles.deadlineSelect}
                value={deadlineDay}
                onChange={(e) => setDeadlineDay(e.target.value)}
                disabled={isSubmitting}
              >
                <option value="">Day</option>
                {Array.from({ length: 31 }, (_, i) => i + 1).map((d) => (
                  <option key={d} value={String(d).padStart(2, '0')}>
                    {d}
                  </option>
                ))}
              </select>
              <input
                className={styles.deadlineSelect}
                value={deadlineYear}
                onChange={(e) => setDeadlineYear(e.target.value)}
                placeholder="Year"
                maxLength={4}
                disabled={isSubmitting}
              />
            </div>
          </div>
        </div>

        <div className={styles.detailRow}>
          <span className={styles.label}>Why are you doing this?</span>
          <div className={styles.whyGrid}>
            {['Make money', 'Creative output', 'Health', 'Joy', 'Family', 'Growth'].map((label) => (
              <button
                key={label}
                type="button"
                className={`${styles.whyBtn} ${why.includes(label) ? styles.whySelected : ''}`}
                onClick={() => toggleWhy(label)}
                disabled={isSubmitting}
              >
                {label}
                {why.includes(label) && <span className={styles.check}>✓</span>}
              </button>
            ))}
          </div>
        </div>

        <div className={styles.detailRow}>
          <span className={styles.label}>Who&apos;s involved?</span>
          <div className={styles.peopleToggle}>
            {(['me', 'others'] as const).map((p) => (
              <button
                key={p}
                type="button"
                className={`${styles.personBtn} ${people === p ? styles.selected : ''}`}
                onClick={() => setPeople(p)}
                disabled={isSubmitting}
              >
                {p === 'me' ? 'Just me' : 'Others too'}
              </button>
            ))}
          </div>
        </div>

        <div className={styles.detailRow}>
          <span className={styles.label}>Files (optional)</span>
          <label className={styles.uploadBtn}>
            Upload
            <input type="file" multiple onChange={(e) => addFiles(e.target.files)} disabled={isSubmitting} />
          </label>
          <div className={styles.fileList}>
            {files.map((file, idx) => (
              <button key={`${file.name}-${idx}`} className={styles.fileChip} type="button" onClick={() => removeFile(idx)}>
                <span>{file.name}</span>
                <span className={styles.remove}>&times;</span>
              </button>
            ))}
          </div>
        </div>
      </div>

      <div className={styles.sectionFooter}>
        <button type="button" className={styles.submitBtn} disabled={!canCreate} onClick={handleCreate}>
          {isSubmitting ? 'Creating…' : 'Create Project'}
        </button>
      </div>
    </div>
  );
}
