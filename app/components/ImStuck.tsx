'use client';

import React, { useState, useEffect, useRef, useCallback } from 'react';
import styles from './ImStuck.module.css';

type StepId =
  | 'reason'
  | 'breathing'
  | 'affirmation'
  | 'journal'
  | 'imagine'
  | 'reset'
  | 'message'
  | 'breakdown'
  | 'microtasks'
  | 'success';

type ReasonType = 'dont-know' | 'overwhelmed' | 'avoiding' | 'waiting';

type Props = {
  open: boolean;
  onClose: () => void;
};

const TASKS = [
  'Open the budget spreadsheet',
  'Find the Q1 totals row',
  'Add one comment about what you notice',
];

export default function ImStuck({ open, onClose }: Props) {
  const [step, setStep] = useState<StepId>('reason');
  const [selectedReason, setSelectedReason] = useState<ReasonType | null>(null);
  const [journalText, setJournalText] = useState('');
  const [currentTask, setCurrentTask] = useState(0);
  const [taskDone, setTaskDone] = useState(false);

  // Breathing state
  const [breathingPhase, setBreathingPhase] = useState('Breathe in');
  const [breathingCount, setBreathingCount] = useState(4);
  const breathingRef = useRef<NodeJS.Timeout | null>(null);

  // Reset state when modal opens
  useEffect(() => {
    if (open) {
      setStep('reason');
      setSelectedReason(null);
      setJournalText('');
      setCurrentTask(0);
      setTaskDone(false);
    }
  }, [open]);

  // Cleanup breathing interval on unmount
  useEffect(() => {
    return () => {
      if (breathingRef.current) {
        clearInterval(breathingRef.current);
      }
    };
  }, []);

  const startBreathing = useCallback(() => {
    const phases = [
      { text: 'Breathe in', duration: 4 },
      { text: 'Hold', duration: 4 },
      { text: 'Breathe out', duration: 6 },
      { text: 'Hold', duration: 2 },
    ];

    let phaseIndex = 0;
    let count = phases[0].duration;
    let cycles = 0;

    setBreathingPhase(phases[0].text);
    setBreathingCount(phases[0].duration);

    breathingRef.current = setInterval(() => {
      count--;

      if (count < 0) {
        phaseIndex++;
        if (phaseIndex >= phases.length) {
          phaseIndex = 0;
          cycles++;
          if (cycles >= 2) {
            if (breathingRef.current) {
              clearInterval(breathingRef.current);
            }
            setStep('affirmation');
            return;
          }
        }
        count = phases[phaseIndex].duration;
      }

      setBreathingPhase(phases[phaseIndex].text);
      setBreathingCount(count);
    }, 1000);
  }, []);

  const handleReasonSelect = (reason: ReasonType) => {
    setSelectedReason(reason);
    setTimeout(() => {
      switch (reason) {
        case 'overwhelmed':
          setStep('breathing');
          startBreathing();
          break;
        case 'avoiding':
          setStep('journal');
          break;
        case 'waiting':
          setStep('reset');
          break;
        case 'dont-know':
          setStep('breakdown');
          break;
      }
    }, 250);
  };

  const handleTaskComplete = () => {
    setTaskDone(true);
    setTimeout(() => {
      if (currentTask >= TASKS.length - 1) {
        setStep('success');
      } else {
        setCurrentTask((prev) => prev + 1);
        setTaskDone(false);
      }
    }, 500);
  };

  const handleCopyMessage = () => {
    const message =
      "Hey! Just checking in on [the thing]. Let me know if you need anything from me. Thanks!";
    navigator.clipboard.writeText(message);
    setStep('success');
  };

  if (!open) return null;

  return (
    <div className={styles.overlay}>
      <button className={styles.closeBtn} onClick={onClose} aria-label="Close">
        <svg viewBox="0 0 24 24" fill="none">
          <path
            d="M18 6L6 18M6 6l12 12"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </svg>
      </button>

      <div className={styles.container}>
        {/* Step 1: Reason Picker */}
        {step === 'reason' && (
          <div className={styles.step}>
            <div className={styles.headerText}>
              <h1 className={styles.title}>
                It&apos;s okay to be <span className={styles.gradient}>stuck.</span>
              </h1>
              <p className={styles.subtitle}>
                Let&apos;s figure out what&apos;s going on and get you back on track.
              </p>
            </div>

            <div className={styles.card}>
              <div className={styles.reasonPills}>
                <button
                  className={`${styles.reasonPill} ${selectedReason === 'dont-know' ? styles.selected : ''}`}
                  onClick={() => handleReasonSelect('dont-know')}
                >
                  I don&apos;t know what to do
                </button>
                <button
                  className={`${styles.reasonPill} ${selectedReason === 'overwhelmed' ? styles.selected : ''}`}
                  onClick={() => handleReasonSelect('overwhelmed')}
                >
                  I feel overwhelmed
                </button>
                <button
                  className={`${styles.reasonPill} ${selectedReason === 'avoiding' ? styles.selected : ''}`}
                  onClick={() => handleReasonSelect('avoiding')}
                >
                  I&apos;m avoiding / procrastinating
                </button>
                <button
                  className={`${styles.reasonPill} ${selectedReason === 'waiting' ? styles.selected : ''}`}
                  onClick={() => handleReasonSelect('waiting')}
                >
                  Waiting on someone / other
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Step: Breathing */}
        {step === 'breathing' && (
          <div className={styles.step}>
            <div className={styles.headerText}>
              <h1 className={styles.title}>
                Let&apos;s <span className={styles.gradient}>breathe.</span>
              </h1>
            </div>

            <div className={styles.card}>
              <div className={styles.breathingContainer}>
                <p className={styles.breathingPhase}>{breathingPhase}</p>
                <p className={styles.breathingCounter}>{breathingCount}</p>
              </div>
            </div>
          </div>
        )}

        {/* Step: Affirmation */}
        {step === 'affirmation' && (
          <div className={styles.step}>
            <div className={styles.headerText}>
              <h1 className={styles.title}>
                You&apos;re doing <span className={styles.gradient}>great.</span>
              </h1>
              <p className={styles.subtitle}>One step at a time.</p>
            </div>

            <div className={styles.card}>
              <div className={styles.infoBox}>
                <p>
                  Feeling overwhelmed is your brain&apos;s way of saying &quot;too much
                  input.&quot; It doesn&apos;t mean you can&apos;t handle it — it means you need
                  to slow down.
                </p>
                <p>
                  Breaking tasks into smaller pieces reduces anxiety and increases completion
                  rates by 70%.
                </p>
                <p>
                  <strong>You&apos;ve got this.</strong>
                </p>
              </div>

              <div className={styles.btnCenter}>
                <button className={styles.btnPrimary} onClick={() => setStep('microtasks')}>
                  Show me what to do →
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Step: Journal */}
        {step === 'journal' && (
          <div className={styles.step}>
            <div className={styles.headerText}>
              <h1 className={styles.title}>
                Let&apos;s be <span className={styles.gradient}>honest.</span>
              </h1>
            </div>

            <div className={styles.card}>
              <p className={styles.journalPrompt}>
                What&apos;s the real reason you&apos;re avoiding this?
              </p>
              <textarea
                className={styles.journalInput}
                placeholder="Be honest with yourself..."
                value={journalText}
                onChange={(e) => setJournalText(e.target.value)}
              />
              <div className={styles.btnCenter}>
                <button className={styles.btnPrimary} onClick={() => setStep('imagine')}>
                  Continue →
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Step: Imagination */}
        {step === 'imagine' && (
          <div className={styles.step}>
            <div className={styles.headerText}>
              <h1 className={styles.title}>
                Close your <span className={styles.gradient}>eyes.</span>
              </h1>
            </div>

            <div className={styles.card}>
              <p className={`${styles.imaginationText} ${styles.primary}`}>
                Imagine it&apos;s tomorrow morning.
              </p>
              <p className={`${styles.imaginationText} ${styles.primary}`}>
                You finished this task.
              </p>
              <p className={styles.imaginationText}>How does it feel? What&apos;s different?</p>
              <p className={styles.imaginationText} style={{ marginTop: 20, marginBottom: 28 }}>
                Hold that feeling. That&apos;s where we&apos;re going.
              </p>

              <div className={styles.btnCenter}>
                <button className={styles.btnPrimary} onClick={() => setStep('microtasks')}>
                  Let&apos;s start small →
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Step: Physical Reset */}
        {step === 'reset' && (
          <div className={styles.step}>
            <div className={styles.headerText}>
              <h1 className={styles.title}>
                Quick <span className={styles.gradient}>reset.</span>
              </h1>
            </div>

            <div className={styles.card}>
              <p className={`${styles.imaginationText} ${styles.primary}`}>Stand up.</p>
              <p className={`${styles.imaginationText} ${styles.primary}`}>
                Roll your shoulders back.
              </p>
              <p className={`${styles.imaginationText} ${styles.primary}`}>
                Take 3 deep breaths.
              </p>
              <p className={styles.imaginationText} style={{ marginTop: 20, marginBottom: 28 }}>
                Sometimes we&apos;re stuck because our body is stuck.
              </p>

              <div className={styles.btnCenter}>
                <button className={styles.btnPrimary} onClick={() => setStep('message')}>
                  Done, what&apos;s next? →
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Step: Message */}
        {step === 'message' && (
          <div className={styles.step}>
            <div className={styles.headerText}>
              <h1 className={styles.title}>
                Send a <span className={styles.gradient}>follow-up?</span>
              </h1>
            </div>

            <div className={styles.card}>
              <div className={styles.messageBox}>
                <p className={styles.messageLabel}>Suggested message</p>
                <p className={styles.messageText}>
                  &quot;Hey! Just checking in on [the thing]. Let me know if you need anything
                  from me. Thanks!&quot;
                </p>
              </div>

              <div className={styles.btnRow}>
                <button className={styles.btnGhost} onClick={() => setStep('success')}>
                  Skip
                </button>
                <button className={styles.btnPrimary} onClick={handleCopyMessage}>
                  Copy &amp; Send
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Step: Breakdown */}
        {step === 'breakdown' && (
          <div className={styles.step}>
            <div className={styles.headerText}>
              <h1 className={styles.title}>
                Let&apos;s <span className={styles.gradient}>break it down.</span>
              </h1>
              <p className={styles.subtitle}>I&apos;ll turn this into tiny, doable steps.</p>
            </div>

            <div className={styles.card}>
              <div className={styles.btnCenter}>
                <button className={styles.btnPrimary} onClick={() => setStep('microtasks')}>
                  Generate microtasks →
                </button>
              </div>

              <button className={styles.askRaimon}>
                <svg
                  width="18"
                  height="18"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                >
                  <circle cx="12" cy="12" r="10" />
                  <path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3" />
                  <line x1="12" y1="17" x2="12.01" y2="17" />
                </svg>
                Or ask Raimon for help
              </button>
            </div>
          </div>
        )}

        {/* Step: Microtasks */}
        {step === 'microtasks' && (
          <div className={styles.step}>
            <div className={styles.headerText}>
              <h1 className={styles.title}>
                One <span className={styles.gradient}>step</span> at a time.
              </h1>
            </div>

            <div className={styles.card}>
              <div className={styles.microtaskContainer}>
                <div className={styles.progressDots}>
                  {TASKS.map((_, i) => (
                    <div
                      key={i}
                      className={`${styles.progressDot} ${
                        i < currentTask ? styles.done : ''
                      } ${i === currentTask ? styles.active : ''}`}
                    />
                  ))}
                </div>

                <p className={styles.microtaskStep}>
                  Step {currentTask + 1} of {TASKS.length}
                </p>
                <p className={styles.microtaskText}>{TASKS[currentTask]}</p>

                <button
                  className={`${styles.microtaskCheck} ${taskDone ? styles.done : ''}`}
                  onClick={handleTaskComplete}
                >
                  <svg viewBox="0 0 24 24" fill="none">
                    <path
                      d="M5 13l4 4L19 7"
                      stroke="currentColor"
                      strokeWidth="2.5"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    />
                  </svg>
                </button>
              </div>

              <div className={styles.backLink}>
                <button className={styles.btnGhost} onClick={() => setStep('reason')}>
                  ← Go back
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Step: Success */}
        {step === 'success' && (
          <div className={styles.step}>
            <div className={styles.headerText}>
              <h1 className={styles.title}>
                You&apos;re <span className={styles.gradient}>back on track!</span>
              </h1>
              <p className={styles.subtitle}>Sometimes all we need is a small reset.</p>
            </div>

            <div className={styles.card}>
              <div className={styles.successEmoji}>🎉</div>
              <div className={styles.btnCenter}>
                <button className={styles.btnSuccess} onClick={onClose}>
                  Return to task →
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
