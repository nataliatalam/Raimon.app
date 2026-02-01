'use client';

import React, { useState, useEffect, useRef, useCallback } from 'react';
import styles from './ActivationFlow.module.css';

type StepId =
  | 'intro'
  | 'breathe'
  | 'move-intro'
  | 'move-exercise'
  | 'walk'
  | 'water'
  | 'chooser'
  | 'creativity'
  | 'journal'
  | 'microtasks'
  | 'success';

type Props = {
  open: boolean;
  onClose: () => void;
  onComplete: () => void;
};

const BREATHING_PHASES = [
  { text: 'Inhale', duration: 5 },
  { text: 'Hold', duration: 2 },
  { text: 'Exhale', duration: 6 },
];

const MOVEMENTS = [
  { title: 'Neck release', action: 'Slow look left, then right', desc: 'Nice and easy', time: 10, color: 'green' },
  { title: 'Shoulder rolls', action: '10 circles, nice and slow', desc: 'Release the tension', time: 10, color: 'blue' },
  { title: 'Chest opener', action: 'Hands behind back, open chest', desc: 'Breathe into it', time: 12, color: 'purple' },
  { title: 'Forward fold', action: 'Soft knees, just hang', desc: 'Let your head drop', time: 12, color: 'orange' },
];

const MICROTASKS = [
  'Open your most important project',
  'Write one sentence about what\'s next',
  'Do the smallest possible action',
];

const JOURNAL_PROMPTS = [
  'What would you tell a friend who felt exactly like you do right now?',
  'What\'s one thing you\'re avoiding — and why does it feel heavy?',
  'What do you actually need right now: rest, clarity, connection, or action?',
  'If this feeling had a message for you, what would it say?',
  'What\'s the smallest thing that would feel like a win today?',
];

const STORY_CONTINUATIONS = [
  'The words on the screen began to shift, rearranging themselves into a question you\'d never dared to ask.',
  'You read it three times. Then you noticed the timestamp — it was sent exactly one year from today, 3:47 AM.',
  'But the strangest part wasn\'t the message. It was the attachment: a photo of somewhere you\'d never been, but somehow recognized.',
];

export default function ActivationFlow({ open, onClose, onComplete }: Props) {
  const [step, setStep] = useState<StepId>('intro');

  // Breathing state
  const [breathingPhase, setBreathingPhase] = useState('Inhale');
  const [breathingCount, setBreathingCount] = useState(5);
  const breathingRef = useRef<NodeJS.Timeout | null>(null);

  // Movement state
  const [currentExercise, setCurrentExercise] = useState(0);
  const [exerciseCountdown, setExerciseCountdown] = useState(MOVEMENTS[0].time);
  const exerciseRef = useRef<NodeJS.Timeout | null>(null);

  // Creativity state
  const [storyText, setStoryText] = useState('');
  const [raimonResponse, setRaimonResponse] = useState('');

  // Journal state
  const [journalText, setJournalText] = useState('');
  const [journalPrompt] = useState(() =>
    JOURNAL_PROMPTS[Math.floor(Math.random() * JOURNAL_PROMPTS.length)]
  );

  // Microtasks state
  const [currentMicrotask, setCurrentMicrotask] = useState(0);
  const [taskDone, setTaskDone] = useState(false);

  // Reset state when modal opens
  useEffect(() => {
    if (open) {
      setStep('intro');
      setBreathingPhase('Inhale');
      setBreathingCount(5);
      setCurrentExercise(0);
      setExerciseCountdown(MOVEMENTS[0].time);
      setStoryText('');
      setRaimonResponse('');
      setJournalText('');
      setCurrentMicrotask(0);
      setTaskDone(false);
    }
  }, [open]);

  // Cleanup intervals on unmount
  useEffect(() => {
    return () => {
      if (breathingRef.current) clearInterval(breathingRef.current);
      if (exerciseRef.current) clearInterval(exerciseRef.current);
    };
  }, []);

  const startBreathing = useCallback(() => {
    let phaseIndex = 0;
    let count = BREATHING_PHASES[0].duration;
    let cycles = 0;

    setBreathingPhase(BREATHING_PHASES[0].text);
    setBreathingCount(BREATHING_PHASES[0].duration);

    breathingRef.current = setInterval(() => {
      count--;

      if (count < 0) {
        phaseIndex++;
        if (phaseIndex >= BREATHING_PHASES.length) {
          phaseIndex = 0;
          cycles++;
          if (cycles >= 3) {
            if (breathingRef.current) {
              clearInterval(breathingRef.current);
            }
            setStep('move-intro');
            return;
          }
        }
        count = BREATHING_PHASES[phaseIndex].duration;
      }

      setBreathingPhase(BREATHING_PHASES[phaseIndex].text);
      setBreathingCount(count);
    }, 1000);
  }, []);

  const skipBreathing = () => {
    if (breathingRef.current) {
      clearInterval(breathingRef.current);
    }
    setStep('move-intro');
  };

  const startMovements = useCallback(() => {
    setStep('move-exercise');
    setCurrentExercise(0);
    setExerciseCountdown(MOVEMENTS[0].time);

    exerciseRef.current = setInterval(() => {
      setExerciseCountdown(prev => {
        if (prev <= 1) {
          setCurrentExercise(current => {
            const nextExercise = current + 1;
            if (nextExercise >= MOVEMENTS.length) {
              if (exerciseRef.current) {
                clearInterval(exerciseRef.current);
              }
              setTimeout(() => setStep('walk'), 300);
              return current;
            }
            setExerciseCountdown(MOVEMENTS[nextExercise].time);
            return nextExercise;
          });
          return prev;
        }
        return prev - 1;
      });
    }, 1000);
  }, []);

  const handleChooserSelect = (choice: 'creativity' | 'journal' | 'microtasks') => {
    setTimeout(() => setStep(choice), 250);
  };

  const pickRandom = () => {
    const options: ('creativity' | 'journal' | 'microtasks')[] = ['creativity', 'journal', 'microtasks'];
    const pick = options[Math.floor(Math.random() * options.length)];
    handleChooserSelect(pick);
  };

  const handleStorySubmit = () => {
    if (storyText.trim().length > 0) {
      const response = STORY_CONTINUATIONS[Math.floor(Math.random() * STORY_CONTINUATIONS.length)];
      setRaimonResponse(response);
    }
  };

  const handleMicrotaskComplete = () => {
    setTaskDone(true);
    setTimeout(() => {
      if (currentMicrotask >= MICROTASKS.length - 1) {
        setStep('success');
      } else {
        setCurrentMicrotask(prev => prev + 1);
        setTaskDone(false);
      }
    }, 500);
  };

  const handleGoToDashboard = () => {
    onClose();
    onComplete();
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
        {/* Intro */}
        {step === 'intro' && (
          <div className={styles.step}>
            <div className={styles.card}>
              <h2 className={styles.introTitle}>
                Okay. <span className={styles.gradient}>Pause for a sec.</span>
              </h2>
              <p className={styles.introSub}>We&apos;ll reset and keep going.</p>
              <button
                className={styles.btnPrimary}
                onClick={() => {
                  setStep('breathe');
                  startBreathing();
                }}
              >
                Start →
              </button>
            </div>
          </div>
        )}

        {/* Breathe */}
        {step === 'breathe' && (
          <div className={styles.step}>
            <div className={styles.headerText}>
              <h1 className={styles.title}>
                Just <span className={styles.gradient}>breathe.</span>
              </h1>
            </div>

            <div className={styles.card}>
              <div className={styles.breathingContainer}>
                <p className={styles.breathingPhase}>{breathingPhase}</p>
                <p className={styles.breathingCounter}>{breathingCount}</p>
              </div>

              <div className={styles.btnRow}>
                <button className={styles.btnGhost} onClick={skipBreathing}>
                  Skip
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Move Intro */}
        {step === 'move-intro' && (
          <div className={styles.step}>
            <div className={styles.headerText}>
              <h1 className={styles.title}>
                Move your body. <span className={styles.gradient}>Tiny.</span>
              </h1>
              <p className={styles.subtitle}>We&apos;re telling your brain: we&apos;re not stuck.</p>
            </div>

            <div className={styles.card}>
              <div style={{ padding: '20px 0' }}>
                <p style={{ fontSize: '15px', color: '#6B6B6B', marginBottom: '24px' }}>
                  4 quick movements. Less than a minute.
                </p>
                <button className={styles.btnPrimary} onClick={startMovements}>
                  Start →
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Move Exercise */}
        {step === 'move-exercise' && (
          <div className={styles.step}>
            <div className={styles.headerText}>
              <h1 className={styles.title}>
                <span className={styles.gradient}>{MOVEMENTS[currentExercise].title}</span>
              </h1>
            </div>

            <div className={styles.card}>
              <div className={styles.moveDisplay}>
                <p className={styles.moveAction}>{MOVEMENTS[currentExercise].action}</p>
                <p className={styles.moveDesc}>{MOVEMENTS[currentExercise].desc}</p>
                <p className={`${styles.moveCountdown} ${styles[MOVEMENTS[currentExercise].color]}`}>
                  {exerciseCountdown}
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Walk */}
        {step === 'walk' && (
          <div className={styles.step}>
            <div className={styles.headerText}>
              <h1 className={styles.title}>
                Almost <span className={styles.gradient}>done.</span>
              </h1>
            </div>

            <div className={styles.card}>
              <div className={styles.walkSuggestion}>
                <div className={styles.walkIcon}>🚶</div>
                <p className={styles.walkText}>If you can: take a quick walk.</p>
                <p className={styles.walkHint}>To the bathroom, the window, or just around the room.</p>
                <button className={styles.btnPrimary} onClick={() => setStep('water')}>
                  Continue →
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Water */}
        {step === 'water' && (
          <div className={styles.step}>
            <div className={styles.headerText}>
              <h1 className={styles.title}>
                One more <span className={styles.gradient}>thing.</span>
              </h1>
            </div>

            <div className={styles.card}>
              <div className={styles.waterContainer}>
                <div className={styles.waterIcon}>💧</div>
                <p className={styles.waterText}>Drink a glass of water.</p>
                <p className={styles.waterHint}>Or 10 big sips if you hate rules.</p>
              </div>

              <div className={styles.btnRow}>
                <button className={styles.btnGhost} onClick={() => setStep('chooser')}>
                  Skip
                </button>
                <button className={styles.btnPrimary} onClick={() => setStep('chooser')}>
                  Done →
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Chooser */}
        {step === 'chooser' && (
          <div className={styles.step}>
            <div className={styles.headerText}>
              <h1 className={styles.title}>
                Okay — what do you <span className={styles.gradient}>want</span> right now?
              </h1>
              <p className={styles.subtitleSmall}>Pick one. I&apos;ll guide the next minute.</p>
            </div>

            <div className={styles.card}>
              <div className={styles.chooserPills}>
                <button className={styles.chooserPill} onClick={() => handleChooserSelect('creativity')}>
                  Make something
                </button>
                <button className={styles.chooserPill} onClick={() => handleChooserSelect('journal')}>
                  Clear my head
                </button>
                <button className={styles.chooserPill} onClick={() => handleChooserSelect('microtasks')}>
                  Tell me the next step
                </button>
              </div>
              <button className={styles.pickForMe} onClick={pickRandom}>
                Not sure — pick for me
              </button>
            </div>
          </div>
        )}

        {/* Creativity */}
        {step === 'creativity' && (
          <div className={styles.step}>
            <div className={styles.headerText}>
              <h1 className={styles.title}>
                Write <span className={styles.gradient}>something.</span>
              </h1>
              <p className={styles.subtitle}>Continue this story however you want.</p>
            </div>

            <div className={styles.card}>
              <div className={styles.storyPrompt}>
                <p className={styles.storyLabel}>Your prompt</p>
                <p className={styles.storyText}>
                  &quot;You open your laptop and there&apos;s a message from yourself, dated next year. It says...&quot;
                </p>
              </div>

              <textarea
                className={styles.textInput}
                placeholder="Continue the story..."
                value={storyText}
                onChange={(e) => setStoryText(e.target.value)}
              />

              {raimonResponse && (
                <div className={styles.raimonResponse}>
                  <p className={styles.raimonLabel}>Raimon continues</p>
                  <p className={styles.raimonText}>{raimonResponse}</p>
                </div>
              )}

              <div className={styles.btnRow}>
                <button className={styles.btnGhost} onClick={() => setStep('chooser')}>
                  ← Back
                </button>
                {!raimonResponse ? (
                  <button className={styles.btnPrimary} onClick={handleStorySubmit}>
                    Send →
                  </button>
                ) : (
                  <button className={styles.btnPrimary} onClick={() => setStep('success')}>
                    Done →
                  </button>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Journal */}
        {step === 'journal' && (
          <div className={styles.step}>
            <div className={styles.headerText}>
              <h1 className={styles.title}>
                Let&apos;s <span className={styles.gradient}>clear</span> your head.
              </h1>
            </div>

            <div className={styles.card}>
              <p className={styles.journalQuestion}>{journalPrompt}</p>

              <textarea
                className={styles.textInput}
                placeholder="Write freely..."
                value={journalText}
                onChange={(e) => setJournalText(e.target.value)}
              />

              <div className={styles.infoBox}>
                <p>
                  Writing externalizes the noise. It doesn&apos;t solve everything — but it creates distance between you and the spiral. That&apos;s often enough to move again.
                </p>
              </div>

              <div className={styles.btnRow}>
                <button className={styles.btnGhost} onClick={() => setStep('chooser')}>
                  ← Back
                </button>
                <button className={styles.btnPrimary} onClick={() => setStep('success')}>
                  Done →
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Microtasks */}
        {step === 'microtasks' && (
          <div className={styles.step}>
            <div className={styles.headerText}>
              <h1 className={styles.title}>
                One <span className={styles.gradient}>step.</span>
              </h1>
            </div>

            <div className={styles.card}>
              <div className={styles.progressDots}>
                {MICROTASKS.map((_, i) => (
                  <div
                    key={i}
                    className={`${styles.progressDot} ${
                      i < currentMicrotask ? styles.done : ''
                    } ${i === currentMicrotask ? styles.active : ''}`}
                  />
                ))}
              </div>

              <p className={styles.microtaskStep}>
                Step {currentMicrotask + 1} of {MICROTASKS.length}
              </p>
              <p className={styles.microtaskText}>{MICROTASKS[currentMicrotask]}</p>

              <button
                className={`${styles.microtaskCheck} ${taskDone ? styles.done : ''}`}
                onClick={handleMicrotaskComplete}
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

              <div className={styles.btnRow}>
                <button className={styles.btnGhost} onClick={() => setStep('chooser')}>
                  ← Back
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Success */}
        {step === 'success' && (
          <div className={styles.step}>
            <div className={styles.headerText}>
              <h1 className={styles.title}>
                You&apos;re <span className={styles.gradient}>moving.</span>
              </h1>
              <p className={styles.subtitle}>That&apos;s all it takes.</p>
            </div>

            <div className={styles.card}>
              <div className={styles.successEmoji}>🎉</div>
              <div className={styles.btnCenter}>
                <button className={styles.btnSuccess} onClick={handleGoToDashboard}>
                  Back to dashboard →
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
