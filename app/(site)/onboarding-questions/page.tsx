'use client';

import { useMemo, useState } from 'react';
import Image from 'next/image';
import styles from './onboardingQuestions.module.css';

type LikeWork = '' | 'yes' | 'ok' | 'no';

const LIFE_OPTIONS = [
  'Student',
  'Employed (job)',
  'Founder / Self-employed',
  'Caregiver',
  'Between jobs / in transition',
  'Other',
] as const;

const GOAL_OPTIONS = [
  'More time / less chaos',
  'Focus / execution',
  'Energy / health',
  'Money / career growth',
  'Creativity / output',
  'Confidence / discipline',
  'Peace / less stress',
  'Relationships',
  'Other',
] as const;

const BREAKER_OPTIONS = [
  "Lack of clarity (don't know what to do first)",
  'Too many responsibilities',
  'Context switching (too many tabs / things at once)',
  'Too many decisions (decision fatigue)',
  'Low energy / bad sleep',
  'Overwhelm (everything feels like a lot)',
  'Procrastination / avoidance',
  'Perfectionism / fear of starting',
  'No system / inconsistency',
  'Other',
] as const;

const TIME_OPTIONS = ['Morning', 'Midday', 'Afternoon', 'Night', 'It varies'] as const;

const BOOST_OPTIONS = [
  'Movement / training',
  'Quiet alone time',
  'Being outside',
  'Music / stimulation',
  'Social time',
  'Building / creating',
  'Cleaning / organizing',
  'Learning something new',
  'Food / cooking',
  'Other',
] as const;

const ENEMY_OPTIONS = [
  'Autopilot living',
  'Doom scrolling',
  'Waiting for motivation',
  'Perfecting instead of shipping',
  'Saying yes to everything',
  'Fear making decisions',
  'Overworking without living',
  'Avoiding the hard thing',
  'Starting → abandoning',
  'Needing approval',
  'Comfort addiction',
  'Other',
] as const;

function cn(...parts: Array<string | false | null | undefined>) {
  return parts.filter(Boolean).join(' ');
}

function clamp(n: number, min: number, max: number) {
  return Math.max(min, Math.min(max, n));
}

type StepIndex = 1 | 2 | 3 | 4 | 5 | 6;

export default function OnboardingQuestions() {
  /**
   * 1 life context
   * 2 goal
   * 3 momentum breakers (merged)
   * 4 power hours (focus + creativity)
   * 5 energy boosts (positive)
   * 6 choose your enemy
   */
  const [step, setStep] = useState<StepIndex>(1);

  const TOTAL_QUESTIONS = 6;

  const [lifeSetup, setLifeSetup] = useState<string[]>([]);
  const [lifeOther, setLifeOther] = useState('');
  const [likesWork, setLikesWork] = useState<LikeWork>('');

  const [goal, setGoal] = useState<string>('');
  const [goalOther, setGoalOther] = useState('');

  const [breakers, setBreakers] = useState<string[]>([]);
  const [breakerOther, setBreakerOther] = useState('');

  const [focusTime, setFocusTime] = useState<string>('');
  const [creativeTime, setCreativeTime] = useState<string>('');

  const [boosts, setBoosts] = useState<string[]>([]);
  const [boostOther, setBoostOther] = useState('');

  const [enemies, setEnemies] = useState<string[]>([]);
  const [enemyOther, setEnemyOther] = useState('');

  const progressFilled = useMemo(() => {
    if (step >= 6) return TOTAL_QUESTIONS;
    return clamp(step, 1, TOTAL_QUESTIONS);
  }, [step]);

  const stepLabel = useMemo(() => {
    return `Step ${step} of ${TOTAL_QUESTIONS}`;
  }, [step]);

  const title = useMemo(() => {
    if (step === 1) return { kicker: stepLabel, h1: 'Your life', sub: 'Give Raimon context. No judging. Just signal.' };
    if (step === 2) return { kicker: stepLabel, h1: 'Your direction', sub: 'Pick one target for the next 8 weeks.' };
    if (step === 3) return { kicker: stepLabel, h1: 'Momentum', sub: 'What breaks it? (Mechanics, not morals.)' };
    if (step === 4) return { kicker: stepLabel, h1: 'Power hours', sub: 'When do you actually win?' };
    if (step === 5) return { kicker: stepLabel, h1: 'Fuel', sub: 'Give Raimon a positive lever.' };
    return { kicker: stepLabel, h1: 'Choose your enemy', sub: 'Name the pattern. Cut the supply.' };
  }, [step, stepLabel]);

  function toggleMulti(value: string, current: string[], set: (v: string[]) => void, max?: number) {
    const exists = current.includes(value);
    if (exists) {
      set(current.filter((x) => x !== value));
      return;
    }
    if (typeof max === 'number' && current.length >= max) return;
    set([...current, value]);
  }

  function selectSingle(value: string, current: string, set: (v: string) => void) {
    set(current === value ? '' : value);
  }

  function next() {
    setStep((s) => clamp((s + 1) as number, 1, 6) as StepIndex);
  }

  function back() {
    setStep((s) => clamp((s - 1) as number, 1, 6) as StepIndex);
  }

  function skip() {
    next();
  }

  const canContinue = useMemo(() => {
    if (step === 1) return lifeSetup.length > 0 || lifeOther.trim().length > 0;
    if (step === 2) return Boolean(goal) || goalOther.trim().length > 0;
    if (step === 3) return breakers.length > 0 || breakerOther.trim().length > 0;
    if (step === 4) return Boolean(focusTime) && Boolean(creativeTime);
    if (step === 5) return boosts.length > 0 || boostOther.trim().length > 0;
    if (step === 6) return enemies.length > 0 || enemyOther.trim().length > 0;
    return true;
  }, [step, lifeSetup, lifeOther, goal, goalOther, breakers, breakerOther, focusTime, creativeTime, boosts, boostOther, enemies, enemyOther]);

  const Pill = ({
    label,
    selected,
    disabled,
    onClick,
  }: {
    label: string;
    selected: boolean;
    disabled?: boolean;
    onClick: () => void;
  }) => (
    <button
      type="button"
      className={cn(styles.pill, selected && styles.pillSelected)}
      onClick={onClick}
      disabled={disabled}
      style={{ opacity: disabled ? 0.55 : 1 }}
    >
      <span>{label}</span>
      {selected && <span className={styles.checkDot}>✓</span>}
    </button>
  );

  return (
    <div className={styles.page}>
      <div className={styles.shell}>
        <div className={styles.aurora} />

        {/* Header */}
        <div className={styles.header}>
          {/* Progress */}
          <div className={styles.progressWrap}>
            {Array.from({ length: TOTAL_QUESTIONS }).map((_, i) => {
              const filled = i < progressFilled;
              return (
                <div key={i} className={styles.progressTrack}>
                  <div className={styles.progressFill} style={{ width: filled ? '100%' : '0%' }} />
                </div>
              );
            })}
          </div>

          {/* Step indicator + Skip */}
          <div className={styles.stepRow}>
            <span className={styles.stepText}>{stepLabel}</span>
            {step < 6 && (
              <button type="button" className={styles.ghostBtn} onClick={skip}>
                Skip
              </button>
            )}
          </div>
        </div>

        {/* Logo cutout */}
        <div className={styles.logoCutout}>
          <div className={styles.logoRow}>
            <Image
              src="/raimon-logo.png"
              alt="Raimon"
              width={110}
              height={110}
              className={styles.logoImage}
            />
          </div>
        </div>

        {/* inner corners */}
        <div className={styles.cornerRight} />
        <div className={styles.cornerBelow} />

        {/* Main content */}
        <div className={styles.mainContent}>
          <div className={styles.contentWrap}>
            <div className={styles.titleBlock}>
              <div className={styles.kicker}>{title.kicker}</div>

              <h1 className={styles.heroTitle}>
                {title.h1.split(' ').map((w, idx, arr) => {
                  const isAccent = idx === arr.length - 1;
                  return (
                    <span key={idx} className={cn(isAccent && styles.heroAccent)}>
                      {w}
                      {idx < arr.length - 1 ? ' ' : ''}
                    </span>
                  );
                })}
              </h1>

              <p className={styles.subText}>{title.sub}</p>
            </div>

            <div className={styles.card}>
              {/* Step 1 */}
              {step === 1 && (
                <div className={styles.stack}>
                  <div className={styles.rowTitle}>Q1) What's your real life setup right now? (choose all that apply)</div>
                  <div className={styles.chipRow}>
                    {LIFE_OPTIONS.map((opt) => (
                      <Pill
                        key={opt}
                        label={opt}
                        selected={lifeSetup.includes(opt)}
                        onClick={() => toggleMulti(opt, lifeSetup, setLifeSetup)}
                      />
                    ))}
                  </div>

                  {lifeSetup.includes('Other') && (
                    <input
                      className={styles.input}
                      placeholder="Write it…"
                      value={lifeOther}
                      onChange={(e) => setLifeOther(e.target.value)}
                    />
                  )}

                  <div className={styles.divider} />

                  <div className={styles.rowTitle}>Optional: Do you like your main work right now?</div>
                  <div className={styles.chipRow}>
                    <Pill label="Yes" selected={likesWork === 'yes'} onClick={() => setLikesWork(likesWork === 'yes' ? '' : 'yes')} />
                    <Pill label="It's okay" selected={likesWork === 'ok'} onClick={() => setLikesWork(likesWork === 'ok' ? '' : 'ok')} />
                    <Pill label="No" selected={likesWork === 'no'} onClick={() => setLikesWork(likesWork === 'no' ? '' : 'no')} />
                  </div>
                </div>
              )}

              {/* Step 2 */}
              {step === 2 && (
                <div className={styles.stack}>
                  <div className={styles.rowTitle}>Q2) In the next 8 weeks, what do you want most? (pick 1)</div>
                  <div className={styles.chipRow}>
                    {GOAL_OPTIONS.map((opt) => (
                      <Pill key={opt} label={opt} selected={goal === opt} onClick={() => selectSingle(opt, goal, setGoal)} />
                    ))}
                  </div>

                  {goal === 'Other' && (
                    <input
                      className={styles.input}
                      placeholder="Name it…"
                      value={goalOther}
                      onChange={(e) => setGoalOther(e.target.value)}
                    />
                  )}
                </div>
              )}

              {/* Step 3 */}
              {step === 3 && (
                <div className={styles.stack}>
                  <div className={styles.rowTitle}>Q3) What breaks your momentum? (pick up to 3)</div>
                  <div className={styles.chipRow}>
                    {BREAKER_OPTIONS.map((opt) => {
                      const selected = breakers.includes(opt);
                      const disabled = !selected && breakers.length >= 3;
                      return (
                        <Pill
                          key={opt}
                          label={opt}
                          selected={selected}
                          disabled={disabled}
                          onClick={() => toggleMulti(opt, breakers, setBreakers, 3)}
                        />
                      );
                    })}
                  </div>

                  {breakers.includes('Other') && (
                    <input
                      className={styles.input}
                      placeholder="Describe it…"
                      value={breakerOther}
                      onChange={(e) => setBreakerOther(e.target.value)}
                    />
                  )}
                </div>
              )}

              {/* Step 4 */}
              {step === 4 && (
                <div className={styles.stack}>
                  <div>
                    <div className={styles.rowTitle}>Q4) Focus is strongest (pick 1)</div>
                    <div className={styles.chipRow}>
                      {TIME_OPTIONS.map((opt) => (
                        <Pill key={opt} label={opt} selected={focusTime === opt} onClick={() => selectSingle(opt, focusTime, setFocusTime)} />
                      ))}
                    </div>
                  </div>

                  <div className={styles.divider} />

                  <div>
                    <div className={styles.rowTitle}>Q4) Creativity is strongest (pick 1)</div>
                    <div className={styles.chipRow}>
                      {TIME_OPTIONS.map((opt) => (
                        <Pill
                          key={`c-${opt}`}
                          label={opt}
                          selected={creativeTime === opt}
                          onClick={() => selectSingle(opt, creativeTime, setCreativeTime)}
                        />
                      ))}
                    </div>
                  </div>
                </div>
              )}

              {/* Step 5 */}
              {step === 5 && (
                <div className={styles.stack}>
                  <div className={styles.rowTitle}>Q5) What gives you energy fast? (pick up to 2)</div>
                  <div className={styles.chipRow}>
                    {BOOST_OPTIONS.map((opt) => {
                      const selected = boosts.includes(opt);
                      const disabled = !selected && boosts.length >= 2;
                      return (
                        <Pill
                          key={opt}
                          label={opt}
                          selected={selected}
                          disabled={disabled}
                          onClick={() => toggleMulti(opt, boosts, setBoosts, 2)}
                        />
                      );
                    })}
                  </div>

                  {boosts.includes('Other') && (
                    <input
                      className={styles.input}
                      placeholder="Name your fuel…"
                      value={boostOther}
                      onChange={(e) => setBoostOther(e.target.value)}
                    />
                  )}
                </div>
              )}

              {/* Step 6 */}
              {step === 6 && (
                <div className={styles.stack}>
                  <div className={styles.rowTitle}>Q6) Choose your enemy. (pick up to 3)</div>
                  <div className={styles.chipRow}>
                    {ENEMY_OPTIONS.map((opt) => {
                      const selected = enemies.includes(opt);
                      const disabled = !selected && enemies.length >= 3;
                      return (
                        <Pill
                          key={opt}
                          label={opt}
                          selected={selected}
                          disabled={disabled}
                          onClick={() => toggleMulti(opt, enemies, setEnemies, 3)}
                        />
                      );
                    })}
                  </div>

                  {enemies.includes('Other') && (
                    <input
                      className={styles.input}
                      placeholder="Name it honestly…"
                      value={enemyOther}
                      onChange={(e) => setEnemyOther(e.target.value)}
                    />
                  )}
                </div>
              )}

              {/* Bottom actions */}
              <div className={styles.actions}>
                <button
                  type="button"
                  className={styles.secondaryBtn}
                  onClick={back}
                  disabled={step === 1}
                >
                  Back
                </button>

                <button
                  type="button"
                  className={styles.primaryBtn}
                  onClick={() => {
                    if (step === 6) {
                      window.location.href = '/onboarding';
                      return;
                    }
                    next();
                  }}
                  disabled={!canContinue}
                >
                  Continue
                </button>
              </div>

              {step >= 1 && step <= 6 && (
                <div className={styles.helper}>
                  Demo-only UI: selections live in component state. Nothing is saved.
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
