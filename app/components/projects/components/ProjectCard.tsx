'use client';

import React from 'react';
import { Eye, Pause, Play, Skull } from 'lucide-react';
import type { Project } from '../types';
import styles from './ProjectCard.module.css';

interface ProjectCardProps {
  project: Project;
  onToggleStatus?: (id: number) => void;
  onKill?: (id: number) => void;
  onView?: (id: number) => void;
  isBeyond?: boolean;
}

export default function ProjectCard({
  project,
  onToggleStatus,
  onKill,
  onView,
  isBeyond = false,
}: ProjectCardProps) {
  const clamped = Math.max(0, Math.min(100, project.progress));
  const pillClass = project.type === 'work' ? styles.pillWork : styles.pillPersonal;
  const strokeColor = project.type === 'work' ? '#171717' : '#FB923C';

  function handleDragStart(e: React.DragEvent) {
    if (isBeyond) return;
    e.dataTransfer.setData('projectId', project.id.toString());
    e.dataTransfer.effectAllowed = 'move';
  }

  return (
    <div
      draggable={!isBeyond}
      onDragStart={handleDragStart}
      className={[
        styles.card,
        isBeyond ? styles.beyond : '',
        !project.active && !isBeyond ? styles.paused : '',
      ].filter(Boolean).join(' ')}
    >
      {/* Outline Progress SVG */}
      {!isBeyond && (
        <svg
          className={styles.progressSvg}
          viewBox="0 0 100 75"
          preserveAspectRatio="none"
          aria-hidden="true"
        >
          {/* track */}
          <rect
            x="2"
            y="2"
            width="96"
            height="71"
            rx="22"
            fill="none"
            stroke="#f5f5f5"
            strokeWidth="4"
          />
          {/* progress */}
          <rect
            x="2"
            y="2"
            width="96"
            height="71"
            rx="22"
            fill="none"
            stroke={strokeColor}
            strokeWidth="4"
            strokeLinecap="round"
            pathLength={100}
            strokeDasharray={100}
            strokeDashoffset={100 - clamped}
            className={styles.progress}
          />
        </svg>
      )}

      {/* Beyond fill */}
      {isBeyond && (
        <div
          className={styles.beyondFill}
          style={{ backgroundColor: project.color }}
          aria-hidden="true"
        />
      )}

      {/* Content */}
      <div className={styles.content}>
        <span className={`${styles.pill} ${pillClass}`}>{project.type}</span>

        <h3 className={styles.title}>{project.name}</h3>

        {isBeyond && <div className={styles.completed}>Completed</div>}
      </div>

      {/* Actions */}
      {!isBeyond && (
        <div className={styles.actions}>
          <button
            type="button"
            onClick={(e) => {
              e.stopPropagation();
              onView?.(project.id);
            }}
            className={styles.iconBtn}
            title="View Project"
            aria-label="View project"
          >
            <Eye size={18} />
          </button>

          <button
            type="button"
            onClick={(e) => {
              e.stopPropagation();
              onToggleStatus?.(project.id);
            }}
            className={[
              styles.primaryBtn,
              project.active ? styles.primaryPause : styles.primaryPlay,
            ].join(' ')}
            title={project.active ? 'Pause Flow' : 'Resume Flow'}
            aria-label={project.active ? 'Pause flow' : 'Resume flow'}
          >
            {project.active ? <Pause size={20} /> : <Play size={20} />}
          </button>

          <button
            type="button"
            onClick={(e) => {
              e.stopPropagation();
              onKill?.(project.id);
            }}
            className={styles.dangerBtn}
            title="Move to Graveyard"
            aria-label="Move to graveyard"
          >
            <Skull size={18} />
          </button>
        </div>
      )}
    </div>
  );
}
