'use client';

import React, { useEffect, useState } from 'react';
import styles from './DaySummary.module.css';

export type DaySummaryData = {
  tasksCompleted: number;
  focusMinutes: number;
  breaks: number;
  streak: number;
  baselinePercent: number;
  weekData: number[]; // 7 values for Mon-Sun, as percentages (0-100)
  thoughts: Thought[];
};

export type Thought = {
  id: string;
  text: string;
};

type Props = {
  data?: DaySummaryData;
  userName?: string;
  onCreateProject?: (thought: Thought) => void;
  onAddToExisting?: (thought: Thought) => void;
  onSaveThought?: (thought: Thought) => void;
  onDiscardThought?: (thought: Thought) => void;
};

const DEFAULT_DATA: DaySummaryData = {
  tasksCompleted: 7,
  focusMinutes: 94,
  breaks: 3,
  streak: 12,
  baselinePercent: 35,
  weekData: [40, 65, 30, 80, 55, 0, 0], // Mon-Sun
  thoughts: [
    {
      id: '1',
      text: '"need to look into payment providers... stripe vs mercadopago... also check compliance requirements for MX"',
    },
    {
      id: '2',
      text: '"call mom about birthday plans, maybe surprise party? check with david first"',
    },
    {
      id: '3',
      text: '"book recommendation: \'Four Thousand Weeks\' by Oliver Burkeman"',
    },
  ],
};

const DAY_LABELS = ['M', 'T', 'W', 'T', 'F', 'S', 'S'];
const STREAK_DAY_LABELS = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];

function getFormattedDate(): string {
  const days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
  const months = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'];
  const now = new Date();
  return `${days[now.getDay()]}, ${months[now.getMonth()]} ${now.getDate()}`;
}

function getTodayIndex(): number {
  // Returns 0-6 for Mon-Sun (weekData format)
  const day = new Date().getDay();
  return day === 0 ? 6 : day - 1;
}

function getStreakDayIndex(): number {
  // Returns 0-6 for Sun-Sat (streak format)
  return new Date().getDay();
}

export default function DaySummary({
  data = DEFAULT_DATA,
  userName = 'Natalia',
  onCreateProject,
  onAddToExisting,
  onSaveThought,
  onDiscardThought,
}: Props) {
  const [animatedBars, setAnimatedBars] = useState(false);
  const todayChartIndex = getTodayIndex();
  const todayStreakIndex = getStreakDayIndex();

  useEffect(() => {
    const timer = setTimeout(() => setAnimatedBars(true), 100);
    return () => clearTimeout(timer);
  }, []);

  // Calculate stroke-dashoffset for the baseline progress ring
  const circumference = 2 * Math.PI * 70; // r=70
  const offset = circumference - (data.baselinePercent / 100) * circumference;

  return (
    <div className={styles.summaryCard}>
      {/* Header Row */}
      <div className={styles.headerRow}>
        <div className={styles.headerLeft}>
          <p className={styles.date}>{getFormattedDate()}</p>
          <h1 className={styles.title}>
            Day Complete<span className={styles.titleAccent}>.</span>
          </h1>
          <p className={styles.subtitle}>Nice work today, {userName}.</p>
        </div>

        <div className={styles.streakWidget}>
          <div className={styles.streakTop}>
            <div className={styles.streakIcon}>🔥</div>
            <div>
              <p className={styles.streakNumber}>{data.streak}</p>
              <p className={styles.streakLabel}>Day Streak</p>
            </div>
          </div>
          <div className={styles.streakDays}>
            {STREAK_DAY_LABELS.map((_, i) => (
              <div
                key={i}
                className={`${styles.streakDash} ${
                  i < todayStreakIndex ? styles.streakDashDone : ''
                } ${i === todayStreakIndex ? styles.streakDashToday : ''}`}
              />
            ))}
          </div>
          <div className={styles.streakDayLabels}>
            {STREAK_DAY_LABELS.map((label, i) => (
              <span
                key={i}
                className={`${styles.streakDayLabel} ${
                  i === todayStreakIndex ? styles.streakDayLabelToday : ''
                }`}
              >
                {label}
              </span>
            ))}
          </div>
        </div>
      </div>

      {/* Main Stats Row */}
      <div className={styles.statsRow}>
        {/* Stats */}
        <div className={styles.statsSection}>
          <p className={styles.sectionLabel}>Today&apos;s Numbers</p>
          <div className={styles.statsGrid}>
            <div className={styles.stat}>
              <p className={`${styles.statValue} ${styles.statGreen}`}>
                {data.tasksCompleted}
              </p>
              <p className={styles.statLabel}>Tasks done</p>
            </div>
            <div className={styles.stat}>
              <p className={`${styles.statValue} ${styles.statBlue}`}>
                {data.focusMinutes}
              </p>
              <p className={styles.statLabel}>Focus mins</p>
            </div>
            <div className={styles.stat}>
              <p className={`${styles.statValue} ${styles.statPurple}`}>
                {data.breaks}
              </p>
              <p className={styles.statLabel}>Breaks</p>
            </div>
          </div>
        </div>

        {/* Week Chart */}
        <div className={styles.chartSection}>
          <p className={styles.sectionLabel}>This Week</p>
          <div className={styles.chartContainer}>
            {data.weekData.map((value, i) => (
              <div key={i} className={styles.chartDay}>
                <div
                  className={`${styles.chartBar} ${
                    i === todayChartIndex ? styles.chartBarToday : ''
                  } ${value === 0 ? styles.chartBarEmpty : ''}`}
                  style={{
                    height: animatedBars ? `${Math.max(value, 10)}px` : '0px',
                    transitionDelay: `${i * 100}ms`,
                  }}
                />
                <span
                  className={`${styles.chartLabel} ${
                    i === todayChartIndex ? styles.chartLabelToday : ''
                  }`}
                >
                  {DAY_LABELS[i]}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Baseline Circle */}
        <div className={styles.baselineSection}>
          <div className={styles.baselineContainer}>
            <svg className={styles.baselineProgressRing} viewBox="0 0 160 160">
              <defs>
                <linearGradient id="baselineGradient" x1="0%" y1="0%" x2="100%" y2="0%">
                  <stop offset="0%" stopColor="#A7F3D0" />
                  <stop offset="50%" stopColor="#93C5FD" />
                  <stop offset="100%" stopColor="#C4B5FD" />
                </linearGradient>
              </defs>
              <circle className={styles.baselineBg} cx="80" cy="80" r="70" />
              <circle
                className={styles.baselineProgress}
                cx="80"
                cy="80"
                r="70"
                style={{
                  strokeDasharray: circumference,
                  strokeDashoffset: offset,
                }}
              />
            </svg>
            <div className={styles.baselineContent}>
              <p className={styles.baselinePercent}>{data.baselinePercent}%</p>
              <p className={styles.baselineTitle}>Building baseline</p>
              <p className={styles.baselineDesc}>Learning your patterns</p>
            </div>
          </div>
        </div>
      </div>

      {/* Thoughts Section */}
      {data.thoughts.length > 0 && (
        <div className={styles.thoughtsSection}>
          <div className={styles.thoughtsBox}>
            <p className={styles.sectionLabel}>Thoughts, notes written.</p>

            <div className={styles.thoughtsGrid}>
              {data.thoughts.map((thought) => (
                <div key={thought.id} className={styles.thoughtCard}>
                  <p className={styles.thoughtText}>{thought.text}</p>
                  <div className={styles.thoughtActions}>
                    <button
                      className={`${styles.thoughtBtn} ${styles.thoughtBtnPrimary}`}
                      onClick={() => onCreateProject?.(thought)}
                      type="button"
                    >
                      Create project
                    </button>
                    <button
                      className={styles.thoughtBtn}
                      onClick={() => onAddToExisting?.(thought)}
                      type="button"
                    >
                      Add to existing
                    </button>
                    <button
                      className={styles.thoughtBtn}
                      onClick={() => onSaveThought?.(thought)}
                      type="button"
                    >
                      Save
                    </button>
                    <button
                      className={`${styles.thoughtBtn} ${styles.thoughtBtnGhost}`}
                      onClick={() => onDiscardThought?.(thought)}
                      type="button"
                    >
                      Discard
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
