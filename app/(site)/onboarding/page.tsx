'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import styles from './onboarding.module.css';

export default function OnboardingPage() {
  const router = useRouter();
  const [currentStep, setCurrentStep] = useState(1);
  const totalSteps = 5;

  const nextStep = () => {
    if (currentStep < totalSteps) {
      setCurrentStep(currentStep + 1);
    }
  };

  const prevStep = () => {
    if (currentStep > 1) {
      setCurrentStep(currentStep - 1);
    }
  };

  return (
    <div className={styles.container}>
      {/* Header */}
      <div className={styles.header}>
        <p className={styles.welcomeLabel}>Welcome to Raimon</p>
        <h1 className={styles.title}>
          Let&apos;s get you<br />started<span>.</span>
        </h1>
      </div>

      {/* Main Card */}
      <div className={styles.mainCard}>
        {/* Steps indicator */}
        <div className={styles.stepsRow}>
          {[1, 2, 3, 4, 5].map((step) => (
            <div
              key={step}
              className={`${styles.stepDash} ${
                step < currentStep ? styles.done : ''
              } ${step === currentStep ? styles.active : ''}`}
            />
          ))}
        </div>

        {/* Step 1: Projects → Tasks → Do */}
        <div className={`${styles.step} ${currentStep === 1 ? styles.activeStep : ''}`}>
          <div className={styles.hierarchyContainer}>
            <div className={styles.hierarchyColumn}>
              <span className={styles.hierarchyWord}>Projects</span>
              <div className={styles.hierarchyLine} />
              <span className={styles.hierarchyDesc}>The big picture</span>
              <div className={styles.hierarchyLine} />
              <span className={styles.exampleLabel}>Example</span>
              <span className={`${styles.hierarchyPill} ${styles.purple}`}>Launch website</span>
            </div>

            <span className={styles.hierarchyArrow}>→</span>

            <div className={styles.hierarchyColumn}>
              <span className={styles.hierarchyWord}>Tasks</span>
              <div className={styles.hierarchyLine} />
              <span className={styles.hierarchyDesc}>Steps to get there</span>
              <div className={styles.hierarchyLine} />
              <span className={styles.exampleLabel}>Example</span>
              <span className={`${styles.hierarchyPill} ${styles.blue}`}>Design homepage</span>
            </div>

            <span className={styles.hierarchyArrow}>→</span>

            <div className={styles.hierarchyColumn}>
              <span className={`${styles.hierarchyWord} ${styles.gradient}`}>Do</span>
              <div className={styles.hierarchyLine} />
              <span className={styles.hierarchyDesc}>Your next action</span>
              <div className={styles.hierarchyLine} />
              <span className={styles.exampleLabel}>Example</span>
              <span className={`${styles.hierarchyPill} ${styles.green}`}>Sketch hero section</span>
            </div>
          </div>

          <div className={styles.navRow}>
            <button className={styles.btnPrimary} onClick={nextStep}>Next →</button>
          </div>
        </div>

        {/* Step 2: Action Buttons */}
        <div className={`${styles.step} ${currentStep === 2 ? styles.activeStep : ''}`}>
          <p className={styles.stepTitle}>What do these buttons do?</p>

          <div className={styles.buttonsGrid}>
            <div className={styles.buttonCard}>
              <div className={styles.buttonCardTop}>
                <span className={`${styles.demoBtn} ${styles.stuck}`}>I&apos;m stuck</span>
              </div>
              <p className={styles.buttonCardText}>
                We&apos;ll help you break it down into smaller pieces or move forward.
              </p>
            </div>

            <div className={styles.buttonCard}>
              <div className={styles.buttonCardTop}>
                <span className={`${styles.demoBtn} ${styles.break}`}>Take a break</span>
              </div>
              <p className={styles.buttonCardText}>
                Even a bathroom break counts. Press it so Raimon can learn how long each task takes you.
              </p>
            </div>

            <div className={styles.buttonCard}>
              <div className={styles.buttonCardTop}>
                <span className={`${styles.demoBtn} ${styles.nothing}`}>I feel like doing nothing</span>
              </div>
              <p className={styles.buttonCardText}>
                Low energy? We&apos;ll help you reset your system and find momentum again.
              </p>
            </div>
          </div>

          <div className={styles.navRow}>
            <button className={styles.btnGhost} onClick={prevStep}>← Back</button>
            <button className={styles.btnPrimary} onClick={nextStep}>Next →</button>
          </div>
        </div>

        {/* Step 3: Daily Check-in */}
        <div className={`${styles.step} ${currentStep === 3 ? styles.activeStep : ''}`}>
          <h2 className={styles.stepBigTitle}>
            Daily <span className={styles.gradientText}>check-in</span>
          </h2>

          <div className={styles.whySection}>
            <p className={styles.whyLabel}>Why is this important to Raimon?</p>
            <p className={styles.whyText}>
              We use your answers to understand your energy and help you plan accordingly.
              If you&apos;re scattered, we&apos;ll suggest smaller tasks. If you&apos;re sharp,
              we&apos;ll prioritize deep work.
            </p>
          </div>

          <div className={styles.navRow}>
            <button className={styles.btnGhost} onClick={prevStep}>← Back</button>
            <button className={styles.btnPrimary} onClick={nextStep}>Next →</button>
          </div>
        </div>

        {/* Step 4: Finish for today */}
        <div className={`${styles.step} ${currentStep === 4 ? styles.activeStep : ''}`}>
          <h2 className={styles.stepBigTitle}>
            Finish for <span className={styles.gradientText}>today</span>
          </h2>

          <div className={styles.finishContent}>
            <p className={styles.finishDesc}>
              When you press <span className={styles.finishBtnInline}>Finish for today</span> you&apos;ll
              see what you accomplished, organize any notes you jotted down, and clear your mind for
              tomorrow. It&apos;s your daily closure ritual.
            </p>
          </div>

          <div className={styles.navRow}>
            <button className={styles.btnGhost} onClick={prevStep}>← Back</button>
            <button className={styles.btnPrimary} onClick={nextStep}>Next →</button>
          </div>
        </div>

        {/* Step 5: Create your first project */}
        <div className={`${styles.step} ${currentStep === 5 ? styles.activeStep : ''}`}>
          <h2 className={styles.stepBigTitle}>
            Let&apos;s create your <span className={styles.gradientText}>first project</span>
          </h2>

          <div className={styles.finishContent}>
            <p className={styles.finishDesc}>
              You&apos;re all set! Now let&apos;s create your first project and start
              turning your goals into action.
            </p>
          </div>

          <div className={styles.navRow}>
            <button type="button" className={styles.btnGhost} onClick={prevStep}>← Back</button>
            <button type="button" className={styles.btnSuccess} onClick={() => router.push('/projects/new')}>Do →</button>
          </div>
        </div>
      </div>
    </div>
  );
}
