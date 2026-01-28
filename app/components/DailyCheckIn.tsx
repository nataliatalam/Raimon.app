import React, { useState, useEffect } from 'react';
import { ArrowLeft, Flame } from 'lucide-react';
import styles from './DailyCheckIn.module.css';
import ActivationFlow from './ActivationFlow';
import { apiFetch, ApiError } from '../../lib/api-client';

// --- Types & Interfaces ---
export interface Option {
  id: string;
  label: string;
  emoji?: string;
}

export interface QuestionStep {
  id: 'energy' | 'mood' | 'focus';
  question: string;
  options: Option[];
}

export interface UserResponses {
  energy?: string;
  mood?: string;
  focus?: string;
}

export enum AppView {
  CHECK_IN = 'CHECK_IN',
  INSIGHT = 'INSIGHT',
}

// --- Constants ---
export const STEPS: QuestionStep[] = [
  {
    id: 'energy',
    question: "How's your energy",
    options: [
      { id: 'low', label: 'Low' },
      { id: 'medium', label: 'Medium' },
      { id: 'high', label: 'High' },
    ]
  },
  {
    id: 'mood',
    question: "How's your mood",
    options: [
      { id: 'down', label: 'Down', emoji: '😔' },
      { id: 'neutral', label: 'Neutral', emoji: '😐' },
      { id: 'good', label: 'Good', emoji: '🙂' },
      { id: 'excellent', label: 'Great', emoji: '🤩' },
    ]
  },
  {
    id: 'focus',
    question: "How's your focus",
    options: [
      { id: 'scattered', label: 'Scattered' },
      { id: 'moderate', label: 'Moderate' },
      { id: 'sharp', label: 'Sharp' },
    ]
  },
];

export const DAYS_OF_WEEK = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];

// --- Sub-Components ---

type StreakWidgetProps = {
  streakCount: number;
};

const StreakWidget: React.FC<StreakWidgetProps> = ({ streakCount }) => {
  const [currentDayIndex, setCurrentDayIndex] = useState<number | null>(null);

  useEffect(() => {
    setCurrentDayIndex(new Date().getDay());
  }, []);

  return (
    <div className={styles.streakSubtle}>
      <div className={styles.streakHeader}>
        <div className={styles.streakIconBox}>
            <Flame className={styles.streakIcon} />
        </div>
        <div>
            <div className={styles.streakCount}>{streakCount}</div>
            <span className={styles.streakLabel}>Day Streak</span>
        </div>
      </div>

      <div className={styles.streakDays}>
        {DAYS_OF_WEEK.map((day, index) => {
          const isToday = currentDayIndex !== null && index === currentDayIndex;
          const isCompleted = currentDayIndex !== null && (index < currentDayIndex || isToday);

          return (
            <div key={index} className={styles.streakDayCol}>
               <div className={`${styles.streakDot} ${isToday ? styles.today : isCompleted ? styles.completed : ''}`} />
               <span className={`${styles.streakDayName} ${isToday ? styles.active : ''}`}>{day}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
};

const Header: React.FC<{ userName?: string; streakCount: number }> = ({ userName, streakCount }) => {
  const [time, setTime] = useState<Date | null>(null);

  useEffect(() => {
    setTime(new Date());
    const timer = setInterval(() => setTime(new Date()), 1000 * 60);
    return () => clearInterval(timer);
  }, []);

  const getGreeting = () => {
    if (!time) return 'Hello';
    const hours = time.getHours();
    if (hours < 12) return 'Good Morning';
    if (hours < 18) return 'Good Afternoon';
    return 'Good Evening';
  };

  const formattedDate = time?.toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric' }) ?? '';

  return (
    <header className={styles.checkinHeader}>
      <div className={styles.headerLeft}>
        <div className={`${styles.dateDisplay} ${styles.slideUp}`} style={{ animationDelay: '0ms' }}>
            <span className={styles.dateText} suppressHydrationWarning>{formattedDate}</span>
            <div className={styles.dateLine}></div>
        </div>
        <h1 className={`${styles.greeting} ${styles.slideUp}`} style={{ animationDelay: '100ms' }}>
          {getGreeting()}<span className={styles.greetingDot}>.</span>
        </h1>
        <p className={`${styles.subGreeting} ${styles.slideUp}`} style={{ animationDelay: '200ms' }}>
          Ready to check in, {userName ?? 'friend'}?
        </p>
      </div>

      <div className={styles.slideUp} style={{ animationDelay: '300ms' }}>
        <StreakWidget streakCount={streakCount} />
      </div>
    </header>
  );
};

// --- Main Component ---

type DailyCheckInProps = {
  onComplete?: () => void;
  userName?: string;
  streakCount?: number;
};

const DailyCheckIn: React.FC<DailyCheckInProps> = ({ onComplete, userName, streakCount = 0 }) => {
  const [currentStepIndex, setCurrentStepIndex] = useState(0);
  const [responses, setResponses] = useState<UserResponses>({});
  const [view, setView] = useState<AppView>(AppView.CHECK_IN);
  const [activationFlowOpen, setActivationFlowOpen] = useState(false);
  const [submitError, setSubmitError] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const currentStep = STEPS[currentStepIndex];
  const isLastStep = currentStepIndex === STEPS.length - 1;

  const handleOptionSelect = (optionId: string) => {
    setResponses(prev => ({
      ...prev,
      [currentStep.id]: optionId
    }));
    
    // Smooth auto-advance
    if (!isLastStep) {
      setTimeout(() => {
        setCurrentStepIndex(prev => prev + 1);
      }, 350);
    }
  };

  const handleBack = () => {
    if (currentStepIndex > 0) {
      setCurrentStepIndex(prev => prev - 1);
    }
  };

  const handleSkip = () => {
    if (onComplete) {
      onComplete();
    } else {
      setView(AppView.INSIGHT);
    }
  };

  function mapEnergy(value?: string) {
    if (value === 'low') return 3;
    if (value === 'high') return 9;
    return 6;
  }

  const handleFinish = async () => {
    if (!responses.energy || !responses.mood || !responses.focus) return;
    setSubmitError('');
    setSubmitting(true);
    try {
      await apiFetch('/api/users/state/check-in', {
        method: 'POST',
        body: {
          energy_level: mapEnergy(responses.energy),
          mood: responses.mood,
          focus_areas: responses.focus ? [responses.focus] : undefined,
        },
      });
      if (onComplete) {
        onComplete();
      } else {
        setView(AppView.INSIGHT);
      }
    } catch (err) {
      if (err instanceof ApiError) setSubmitError(err.message);
      else setSubmitError('Failed to record check-in.');
    } finally {
      setSubmitting(false);
    }
  };

  const renderStepIndicator = () => (
    <div className={styles.stepIndicator}>
      {STEPS.map((_, idx) => (
        <div 
          key={idx} 
          className={`${styles.stepDot} ${idx === currentStepIndex ? styles.active : ''}`}
        />
      ))}
    </div>
  );

  return (
    <div className={styles.container}>
      <div className={styles.checkinPage}>
        {/* Decorative Background */}
        <div className={styles.gradientOrb}></div>

        {view === AppView.CHECK_IN && <Header userName={userName} streakCount={streakCount} />}

        <main className={styles.checkinContent}>
          {view === AppView.CHECK_IN && (
            <div className={styles.questionContainer}>
              
              {renderStepIndicator()}

              {/* Question Title */}
              <div className={styles.slideUp} style={{ animationDelay: '100ms' }}>
                <p className={styles.questionLabel}>
                  CHECK-IN
                </p>
                <h2 className={styles.questionText}>
                  {currentStep.question}
                  <span className={styles.cursor}>|</span>
                </h2>
              </div>

              {/* Options Rendering */}
              <div className={styles.slideUp} style={{ animationDelay: '200ms' }}>
                
                {/* LAYOUT: MOOD (Grid of Cards) */}
                {currentStep.id === 'mood' ? (
                  <div className={styles.emojiGrid}>
                    {currentStep.options.map((option) => {
                      const isSelected = responses[currentStep.id] === option.id;
                      return (
                        <button
                          key={option.id}
                          onClick={() => handleOptionSelect(option.id)}
                          className={`${styles.emojiCard} ${isSelected ? styles.selected : ''}`}
                        >
                          <span className={styles.emojiIcon}>{option.emoji}</span>
                          <span className={styles.emojiLabel}>{option.label}</span>
                        </button>
                      );
                    })}
                  </div>
                ) : (
                  /* LAYOUT: ENERGY & FOCUS (Row of Pills) */
                  <div className={styles.optionsContainer}>
                    {currentStep.options.map((option) => {
                      const isSelected = responses[currentStep.id] === option.id;
                      return (
                        <button
                          key={option.id}
                          onClick={() => handleOptionSelect(option.id)}
                          className={`${styles.optionPill} ${isSelected ? styles.selected : ''}`}
                        >
                          {option.label}
                        </button>
                      );
                    })}
                  </div>
                )}
              </div>
            </div>
          )}

          {view === AppView.INSIGHT && (
            <div className={`${styles.insightContainer} ${styles.slideUp}`}>
               {/* Blank Dashboard Placeholder */}
               <div className={styles.dashboardPlaceholder}>
                  <h2 className={styles.dashboardTitle}>Dashboard</h2>
               </div>
            </div>
          )}
        </main>

        {/* Footer Navigation */}
        {view === AppView.CHECK_IN && (
          <footer className={styles.checkinFooter}>
            {/* LEFT: Back Button */}
            <div className={styles.footerLeft}>
              <button 
                onClick={handleBack}
                className={`${styles.backBtn} ${currentStepIndex > 0 ? styles.visible : ''}`}
              >
                <ArrowLeft size={18} /> Back
              </button>
            </div>

            {/* CENTER: I feel like doing nothing (Only on last step) */}
            <div className={styles.footerCenter}>
              {isLastStep && (
                <button
                  className={styles.nothingBtn}
                  onClick={() => setActivationFlowOpen(true)}
                >
                  I feel like doing nothing
                </button>
              )}
            </div>

            {/* RIGHT: Action Button */}
            <div className={styles.footerRight}>
              {isLastStep ? (
                <button
                  onClick={handleFinish}
                  disabled={!responses[currentStep.id] || submitting}
                  className={styles.primaryBtn}
                >
                  {submitting ? 'Saving…' : 'Go to dashboard'}
                </button>
              ) : (
                <button 
                  onClick={handleSkip}
                  className={styles.skipBtn}
                >
                  Skip check-in
                </button>
              )}
            </div>
          </footer>
        )}

        {submitError && <div className={styles.errorMessage}>{submitError}</div>}

        <ActivationFlow
          open={activationFlowOpen}
          onClose={() => setActivationFlowOpen(false)}
          onComplete={handleFinish}
        />
      </div>
    </div>
  );
};

export default DailyCheckIn;
