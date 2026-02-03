'use client';

import React, { useState } from 'react';
import { Sparkles, Play, RefreshCw, ChevronRight } from 'lucide-react';
import { apiFetch, ApiError } from '../../lib/api-client';
import styles from './NextDo.module.css';

interface ActiveDo {
  task_id: string;
  task_title: string;
  reason_codes: string[];
  alt_task_ids: string[];
  selected_at: string;
}

interface CoachMessage {
  title: string;
  message: string;
  next_step: string;
}

interface NextDoResponse {
  success: boolean;
  data: {
    active_do: ActiveDo;
    coach_message: CoachMessage;
  };
  error?: string;
}

interface Props {
  onStartTask?: (taskId: string, taskTitle: string) => void;
}

const REASON_LABELS: Record<string, string> = {
  deadline_urgent: 'Due soon',
  deadline_soon: 'Upcoming deadline',
  priority_high: 'High priority',
  priority_medium: 'Medium priority',
  energy_fit: 'Matches your energy',
  time_fit: 'Fits your time',
  mode_fit: 'Aligns with your mode',
  progress_continuation: 'Already started',
};

export default function NextDo({ onStartTask }: Props) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [activeDo, setActiveDo] = useState<ActiveDo | null>(null);
  const [coachMessage, setCoachMessage] = useState<CoachMessage | null>(null);
  const [hasRequested, setHasRequested] = useState(false);

  async function fetchNextDo() {
    setLoading(true);
    setError('');
    try {
      const response = await apiFetch<NextDoResponse>('/api/agent-mvp/next-do', {
        method: 'POST',
        body: {},
      });

      if (response.success && response.data) {
        setActiveDo(response.data.active_do);
        setCoachMessage(response.data.coach_message);
      } else {
        setError(response.error || 'Failed to get recommendation');
      }
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError('Failed to get AI recommendation');
      }
    } finally {
      setLoading(false);
      setHasRequested(true);
    }
  }

  function handleStart() {
    if (activeDo && onStartTask) {
      onStartTask(activeDo.task_id, activeDo.task_title);
    }
  }

  function handleRefresh() {
    setActiveDo(null);
    setCoachMessage(null);
    fetchNextDo();
  }

  // Initial state - show prompt to get recommendation
  if (!hasRequested && !activeDo) {
    return (
      <div className={styles.container}>
        <div className={styles.promptCard}>
          <div className={styles.iconWrapper}>
            <Sparkles size={24} />
          </div>
          <h3 className={styles.promptTitle}>Not sure what to work on?</h3>
          <p className={styles.promptDesc}>
            Let AI analyze your tasks and energy level to recommend the best thing to do right now.
          </p>
          <button
            className={styles.primaryBtn}
            onClick={fetchNextDo}
            disabled={loading}
          >
            {loading ? (
              <>
                <RefreshCw size={18} className={styles.spin} />
                Thinking...
              </>
            ) : (
              <>
                <Sparkles size={18} />
                Get AI Recommendation
              </>
            )}
          </button>
        </div>
      </div>
    );
  }

  // Loading state
  if (loading) {
    return (
      <div className={styles.container}>
        <div className={styles.loadingCard}>
          <RefreshCw size={32} className={styles.spin} />
          <p>Analyzing your tasks...</p>
        </div>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className={styles.container}>
        <div className={styles.errorCard}>
          <p className={styles.errorText}>{error}</p>
          <button className={styles.retryBtn} onClick={handleRefresh}>
            <RefreshCw size={16} />
            Try again
          </button>
        </div>
      </div>
    );
  }

  // Success state - show recommendation
  if (activeDo && coachMessage) {
    return (
      <div className={styles.container}>
        <div className={styles.recommendationCard}>
          <div className={styles.header}>
            <div className={styles.aiLabel}>
              <Sparkles size={14} />
              AI Recommendation
            </div>
            <button className={styles.refreshBtn} onClick={handleRefresh} title="Get new recommendation">
              <RefreshCw size={16} />
            </button>
          </div>

          <h3 className={styles.coachTitle}>{coachMessage.title}</h3>
          <p className={styles.coachMessage}>{coachMessage.message}</p>

          <div className={styles.taskCard}>
            <div className={styles.taskTitle}>{activeDo.task_title}</div>
            <div className={styles.reasonTags}>
              {activeDo.reason_codes.slice(0, 2).map((code) => (
                <span key={code} className={styles.reasonTag}>
                  {REASON_LABELS[code] || code}
                </span>
              ))}
            </div>
          </div>

          <div className={styles.nextStep}>
            <ChevronRight size={16} />
            <span>{coachMessage.next_step}</span>
          </div>

          <button className={styles.startBtn} onClick={handleStart}>
            <Play size={18} />
            Start this task
          </button>
        </div>
      </div>
    );
  }

  return null;
}
