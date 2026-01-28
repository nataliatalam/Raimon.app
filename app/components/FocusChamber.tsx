'use client';

import React, { useMemo, useState } from 'react';
import styles from './FocusChamber.module.css';

export type FocusTask = {
  title: string; // use "\n" for line breaks
  desc: string;
  project: string;
  duration?: string; // optional (e.g. "25 min")
};

export type FocusResource = {
  id: string;
  kind: 'doc' | 'sheet' | 'link';
  name: string;
  action?: string; // e.g. "View document"
  onClick?: () => void;
};

type Props = {
  task: FocusTask;
  resources?: FocusResource[];

  onSend?: (text: string) => void;

  onStuck?: () => void;
  onBreak?: () => void;
  onResume?: () => void;
  onDone?: () => void;
};

export default function FocusChamber({
  task,
  resources = [],
  onSend,
  onStuck,
  onBreak,
  onResume,
  onDone,
}: Props) {
  const [text, setText] = useState('');
  const [isOnBreak, setIsOnBreak] = useState(false);

  const hasResources = resources.length > 0;

  const projectDotClass = useMemo(() => styles.projectDot, []);

  function handleSend() {
    const msg = text.trim();
    if (!msg) return;
    onSend?.(msg);
    setText('');
  }

  const handleBreakToggle = () => {
    if (isOnBreak) {
      setIsOnBreak(false);
      onResume?.();
    } else {
      setIsOnBreak(true);
      onBreak?.();
    }
  };

  return (
    <div className={`${styles.page} ${isOnBreak ? styles.breakMode : ''}`}>
      {isOnBreak && <div className={styles.breakOverlay} />}
      {/* Header */}
      <header className={styles.header}>
        <div>
          <div className={styles.pageLabel}>Focus Chamber</div>
          <div className={styles.pageTitle}>Stay focused</div>
        </div>
      </header>

      {/* Main */}
      <div className={styles.main}>
        {/* Left */}
        <section className={styles.left}>
          <div className={styles.taskSection}>
            <div className={styles.projectPill}>
              <span className={projectDotClass} />
              <span className={styles.projectName}>{task.project}</span>
            </div>

            <h1 className={styles.taskTitle}>{task.title}</h1>
            <p className={styles.taskDesc}>{task.desc}</p>

            {/* ✅ Resources NOW sit right under the task text */}
            {hasResources ? (
              <div className={styles.resources}>
                <div className={styles.sectionLabel}>Related resources</div>

                <div className={styles.resourcesList}>
                  {resources.map((r) => (
                    <button
                      key={r.id}
                      type="button"
                      className={styles.resourcePill}
                      onClick={r.onClick}
                    >
                      <span
                        className={[
                          styles.resourceIconCircle,
                          r.kind === 'doc' ? styles.iconDoc : '',
                          r.kind === 'sheet' ? styles.iconSheet : '',
                          r.kind === 'link' ? styles.iconLink : '',
                        ].join(' ')}
                      >
                        {r.kind === 'doc' && (
                          <svg
                            xmlns="http://www.w3.org/2000/svg"
                            fill="none"
                            viewBox="0 0 24 24"
                            stroke="currentColor"
                          >
                            <path
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              strokeWidth="1.6"
                              d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                            />
                          </svg>
                        )}
                        {r.kind === 'sheet' && (
                          <svg
                            xmlns="http://www.w3.org/2000/svg"
                            fill="none"
                            viewBox="0 0 24 24"
                            stroke="currentColor"
                          >
                            <path
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              strokeWidth="1.6"
                              d="M3 10h18M3 14h18m-9-4v8m-7 0h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z"
                            />
                          </svg>
                        )}
                        {r.kind === 'link' && (
                          <svg
                            xmlns="http://www.w3.org/2000/svg"
                            fill="none"
                            viewBox="0 0 24 24"
                            stroke="currentColor"
                          >
                            <path
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              strokeWidth="1.6"
                              d="M13.828 10.172a4 4 0 010 5.656l-1.414 1.414a4 4 0 01-5.656-5.656l1.414-1.414a4 4 0 015.656 0M10.172 13.828a4 4 0 010-5.656l1.414-1.414a4 4 0 015.656 5.656l-1.414 1.414a4 4 0 01-5.656 0"
                            />
                          </svg>
                        )}
                      </span>

                      <span className={styles.resourceText}>
                        <span className={styles.resourceName}>{r.name}</span>
                        <span className={styles.resourceAction}>{r.action ?? 'Open'}</span>
                      </span>
                    </button>
                  ))}
                </div>
              </div>
            ) : null}
          </div>
        </section>

        {/* Right */}
        <aside className={styles.right}>
          <div className={styles.raimonBox}>
            <div className={styles.raimonMessage}>
              <div className={styles.raimonGreeting}>Ready to help you with this task.</div>
              <div className={styles.raimonSubtext}>
                I can summarize the docs, find key numbers, or help you write comments.
              </div>
            </div>

            <div className={styles.inputRow}>
              <input
                value={text}
                onChange={(e) => setText(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') handleSend();
                }}
                placeholder="Ask anything..."
              />
              <button
                type="button"
                className={styles.sendBtn}
                onClick={handleSend}
                aria-label="Send"
              >
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M14 5l7 7m0 0l-7 7m7-7H3" />
                </svg>
              </button>
            </div>
          </div>

          <div className={styles.actionsRow}>
            <button type="button" className={[styles.actionBtn, styles.btnOutline].join(' ')} onClick={onStuck}>
              I&apos;m stuck
            </button>
            <button
              type="button"
              className={[
                styles.actionBtn,
                isOnBreak ? styles.btnImBack : styles.btnBlue,
              ].join(' ')}
              onClick={handleBreakToggle}
            >
              {isOnBreak ? "I'm back" : 'Take a break'}
            </button>
            <button type="button" className={[styles.actionBtn, styles.btnOrange].join(' ')} onClick={onDone}>
              Done
            </button>
          </div>
        </aside>
      </div>
    </div>
  );
}
