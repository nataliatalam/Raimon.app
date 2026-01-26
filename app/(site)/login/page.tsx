'use client';

import { useState } from 'react';
import type { FormEvent } from 'react';
import Link from 'next/link';
import Image from 'next/image';
import { useRouter } from 'next/navigation';
import styles from './login.module.css';

type Step = 'auth' | 'verify';

export default function LoginPage() {
  const router = useRouter();

  const [step, setStep] = useState<Step>('auth');
  const [isLoginMode, setIsLoginMode] = useState(true);

  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  // UI message box
  const [error, setError] = useState('');

  // Form state
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [name, setName] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');

  // Verify state
  const [pendingEmail, setPendingEmail] = useState('');
  const [verificationCode, setVerificationCode] = useState('');

  const isVerify = step === 'verify';

  const toggleMode = () => {
    setError('');
    setStep('auth');
    setVerificationCode('');
    setPendingEmail('');
    setIsLoginMode((v) => !v);
  };

  const togglePassword = () => setShowPassword((v) => !v);

  function fakeDelay(ms = 650) {
    return new Promise<void>((res) => setTimeout(res, ms));
  }

  function goDashboard() {
    router.push('/dashboard');
  }

  function goOnboarding() {
    router.push('/onboarding-questions');
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError('');

    // Basic demo validation (keep it simple)
    if (!email.trim() || !password.trim()) {
      setError('Please fill in all fields');
      return;
    }

    if (!isLoginMode) {
      if (!name.trim()) {
        setError('Please enter your name');
        return;
      }
      if (password !== confirmPassword) {
        setError('Passwords do not match');
        return;
      }
      if (password.length < 6) {
        setError('Password must be at least 6 characters');
        return;
      }
    }

    setIsLoading(true);
    try {
      await fakeDelay();

      if (isLoginMode) {
        // ✅ Demo login: always succeeds
        goDashboard();
        return;
      }

      // ✅ Demo signup: show verify UI (no real email sent)
      setPendingEmail(email.trim());
      setStep('verify');
      setError('Demo mode: no email is sent. Enter any code (try 123456) to continue.');
    } finally {
      setIsLoading(false);
    }
  }

  async function handleVerify(e: FormEvent) {
    e.preventDefault();
    setError('');

    if (!pendingEmail) {
      setError('Missing email. Go back and sign up again.');
      return;
    }
    if (!verificationCode.trim()) {
      setError('Enter any code for demo (try 123456).');
      return;
    }

    setIsLoading(true);
    try {
      await fakeDelay();
      // ✅ Demo verify: always succeeds
      goOnboarding();
    } finally {
      setIsLoading(false);
    }
  }

  async function handleResendCode() {
    setError('');
    if (!pendingEmail) return;

    setIsLoading(true);
    try {
      await fakeDelay(450);
      setError('Demo mode: code “resent”. Use any code to continue.');
    } finally {
      setIsLoading(false);
    }
  }

  async function handleGoogleSignIn() {
    setError('');
    setIsLoading(true);
    try {
      await fakeDelay(650);
      // ✅ Demo Google: send to onboarding (feels like first-time flow)
      goOnboarding();
    } finally {
      setIsLoading(false);
    }
  }

  const goBackToSignup = () => {
    setError('');
    setStep('auth');
    setIsLoginMode(false);
    setVerificationCode('');
  };

  return (
    <>
      {/* Desktop Version */}
      <div className={styles.desktopContainer}>
        <div className={styles.mainContainer}>
          <div className={styles.aurora} />

          <div className={styles.header}>
            <div className={styles.navDesktop}>
              <div className={styles.navRight}>
                {!isVerify && (
                  <>
                    <span className={styles.navText}>
                      {isLoginMode ? "Don't have an account?" : 'Already have an account?'}
                    </span>
                    <button className={styles.navBtn} onClick={toggleMode} type="button" disabled={isLoading}>
                      {isLoginMode ? 'Sign up' : 'Log in'}
                    </button>
                  </>
                )}
              </div>
            </div>
          </div>

          <div className={styles.logoCutout}>
            <Link href="/" className={styles.logoLink}>
              <Image
                src="/raimon-logo.png"
                alt="Raimon"
                width={140}
                height={48}
                className={styles.logoImg}
                priority
              />
            </Link>
          </div>

          <div className={styles.cornerRight} />
          <div className={styles.cornerBelow} />

          <div className={styles.mainContent}>
            <div className={styles.twoColumnLayout}>
              <div className={styles.brandingColumn}>
                <div className={styles.verificationPill}>
                  <div className={styles.pillIcon}>
                    <svg width="8" height="8" viewBox="0 0 24 24" fill="none">
                      <path
                        d="M5 12L10 17L20 7"
                        stroke="white"
                        strokeWidth="3"
                        strokeLinecap="round"
                        strokeLinejoin="round"
                      />
                    </svg>
                  </div>
                  <span className={styles.pillText}>Achieve your goals with AI</span>
                </div>

                <h1 className={styles.heroTitle}>
                  {isVerify ? (
                    <>
                      Enter<br />
                      <span className={styles.heroGradient}>code</span>
                    </>
                  ) : isLoginMode ? (
                    <>
                      Welcome<br />
                      <span className={styles.heroGradient}>back!</span>
                    </>
                  ) : (
                    <>
                      Start your<br />
                      <span className={styles.heroGradient}>journey!</span>
                    </>
                  )}
                </h1>
              </div>

              <div className={styles.formCard}>
                <h2 className={styles.formTitle}>
                  {isVerify ? 'Enter code' : isLoginMode ? 'Log in' : 'Create account'}
                </h2>

                <form onSubmit={isVerify ? handleVerify : handleSubmit} className={styles.formContent}>
                  {isVerify ? (
                    <>
                      <div>
                        <label className={styles.formLabel}>Verification code</label>
                        <input
                          type="text"
                          inputMode="numeric"
                          className={styles.formInput}
                          placeholder="Enter any code (demo)"
                          value={verificationCode}
                          onChange={(e) =>
                            setVerificationCode(e.target.value.replace(/[^\d]/g, '').slice(0, 10))
                          }
                        />
                        <div style={{ marginTop: 8, fontSize: 12, opacity: 0.7 }}>
                          Sent to: <b>{pendingEmail}</b>
                        </div>
                      </div>

                      {error && (
                        <div className={styles.errorBox}>
                          <p className={styles.errorText}>{error}</p>
                        </div>
                      )}

                      <div style={{ display: 'flex', justifyContent: 'space-between', gap: 12, marginTop: 8 }}>
                        <button
                          type="button"
                          className={styles.navBtn}
                          onClick={goBackToSignup}
                          disabled={isLoading}
                        >
                          Back
                        </button>

                        <button
                          type="button"
                          className={styles.navBtn}
                          onClick={handleResendCode}
                          disabled={isLoading}
                        >
                          Resend code
                        </button>
                      </div>

                      <button type="submit" className={styles.submitBtn} disabled={isLoading}>
                        {isLoading ? 'Verifying...' : 'Verify code'}
                      </button>

                      <button
                        type="button"
                        className={styles.googleBtn}
                        onClick={goOnboarding}
                        disabled={isLoading}
                        style={{ marginTop: 8 }}
                      >
                        Skip for demo
                      </button>

                      <div className={styles.bottomSignup}>
                        <span className={styles.bottomSignupText}>Already have an account? </span>
                        <button
                          type="button"
                          className={styles.bottomSignupLink}
                          onClick={() => {
                            setError('');
                            setStep('auth');
                            setIsLoginMode(true);
                          }}
                        >
                          Log in
                        </button>
                      </div>
                    </>
                  ) : (
                    <>
                      {!isLoginMode && (
                        <div>
                          <label className={styles.formLabel}>Full name</label>
                          <input
                            type="text"
                            className={styles.formInput}
                            placeholder="Your name"
                            value={name}
                            onChange={(e) => setName(e.target.value)}
                          />
                        </div>
                      )}

                      <div>
                        <label className={styles.formLabel}>Email address</label>
                        <input
                          type="email"
                          className={styles.formInput}
                          placeholder="you@email.com"
                          value={email}
                          onChange={(e) => setEmail(e.target.value)}
                          required
                        />
                      </div>

                      <div>
                        <label className={styles.formLabel}>Password</label>
                        <div className={styles.passwordWrapper}>
                          <input
                            type={showPassword ? 'text' : 'password'}
                            className={`${styles.formInput} ${styles.passwordInput}`}
                            placeholder="••••••••"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            required
                          />
                          <button type="button" className={styles.passwordToggle} onClick={togglePassword}>
                            {showPassword ? (
                              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24" />
                                <line x1="1" y1="1" x2="23" y2="23" />
                              </svg>
                            ) : (
                              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
                                <circle cx="12" cy="12" r="3" />
                              </svg>
                            )}
                          </button>
                        </div>
                      </div>

                      {!isLoginMode && (
                        <div>
                          <label className={styles.formLabel}>Confirm password</label>
                          <input
                            type={showPassword ? 'text' : 'password'}
                            className={styles.formInput}
                            placeholder="••••••••"
                            value={confirmPassword}
                            onChange={(e) => setConfirmPassword(e.target.value)}
                          />
                        </div>
                      )}

                      {error && (
                        <div className={styles.errorBox}>
                          <p className={styles.errorText}>{error}</p>
                        </div>
                      )}

                      {isLoginMode && (
                        <div className={styles.rememberRow}>
                          <label className={styles.rememberLabel}>
                            <input type="checkbox" className={styles.rememberCheckbox} defaultChecked />
                            <span className={styles.rememberText}>Remember me</span>
                          </label>

                          {/* ✅ no route for demo */}
                          <button
                            type="button"
                            className={styles.forgotLink}
                            onClick={() => setError('Demo mode: password reset is not enabled.')}
                          >
                            Forgot password?
                          </button>
                        </div>
                      )}

                      <button type="submit" className={styles.submitBtn} disabled={isLoading}>
                        {isLoading
                          ? isLoginMode
                            ? 'Logging in...'
                            : 'Creating account...'
                          : isLoginMode
                          ? 'Log in'
                          : 'Create account'}
                      </button>

                      <div className={styles.divider}>
                        <div className={styles.dividerLine} />
                        <span className={styles.dividerText}>or continue with</span>
                        <div className={styles.dividerLine} />
                      </div>

                      <button type="button" className={styles.googleBtn} onClick={handleGoogleSignIn} disabled={isLoading}>
                        <svg width="18" height="18" viewBox="0 0 24 24">
                          <path
                            fill="#4285F4"
                            d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
                          />
                          <path
                            fill="#34A853"
                            d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                          />
                          <path
                            fill="#FBBC05"
                            d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
                          />
                          <path
                            fill="#EA4335"
                            d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
                          />
                        </svg>
                        Continue with Google
                      </button>

                      <div className={styles.bottomSignup}>
                        <span className={styles.bottomSignupText}>
                          {isLoginMode ? "Don't have an account? " : 'Already have an account? '}
                        </span>
                        <button type="button" className={styles.bottomSignupLink} onClick={toggleMode} disabled={isLoading}>
                          {isLoginMode ? 'Join Raimon' : 'Log in'}
                        </button>
                      </div>
                    </>
                  )}
                </form>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Mobile Version */}
      <div className={styles.mobileContainer}>
        <div className={styles.mobileAurora} />

        <div className={styles.mobileHeader}>
          <div className={styles.mobileLogo}>
            <Image
              src="/raimon-logo.png"
              alt="Raimon"
              width={140}
              height={48}
              className={styles.mobileLogoImg}
              priority
            />
          </div>

          <h1 className={styles.mobileTitle}>
            {isVerify ? (
              <>
                Enter<br />
                <span className={styles.mobileTitleGradient}>code</span>
              </>
            ) : isLoginMode ? (
              <>
                Welcome<br />
                <span className={styles.mobileTitleGradient}>back!</span>
              </>
            ) : (
              <>
                Start your<br />
                <span className={styles.mobileTitleGradient}>journey!</span>
              </>
            )}
          </h1>
        </div>

        <div className={styles.mobileCard}>
          <form className={styles.mobileForm} onSubmit={isVerify ? handleVerify : handleSubmit}>
            {isVerify ? (
              <>
                <div>
                  <label className={styles.mobileFieldLabel}>Verification code</label>
                  <input
                    type="text"
                    inputMode="numeric"
                    className={styles.mobileInput}
                    placeholder="Enter any code (demo)"
                    value={verificationCode}
                    onChange={(e) =>
                      setVerificationCode(e.target.value.replace(/[^\d]/g, '').slice(0, 10))
                    }
                  />
                </div>

                {error && (
                  <div className={styles.mobileError}>
                    <p className={styles.mobileErrorText}>{error}</p>
                  </div>
                )}

                <div style={{ display: 'flex', justifyContent: 'space-between', gap: 12 }}>
                  <button type="button" className={styles.mobileSubmit} onClick={goBackToSignup} disabled={isLoading}>
                    Back
                  </button>
                  <button type="button" className={styles.mobileSubmit} onClick={handleResendCode} disabled={isLoading}>
                    Resend
                  </button>
                </div>

                <button type="submit" className={styles.mobileSubmit} disabled={isLoading}>
                  {isLoading ? 'Verifying...' : 'Verify code'}
                </button>

                <button type="button" className={styles.mobileGoogle} onClick={goOnboarding} disabled={isLoading}>
                  Skip for demo
                </button>
              </>
            ) : (
              <>
                {!isLoginMode && (
                  <div>
                    <label className={styles.mobileFieldLabel}>Full name</label>
                    <input
                      type="text"
                      className={styles.mobileInput}
                      placeholder="Your name"
                      value={name}
                      onChange={(e) => setName(e.target.value)}
                    />
                  </div>
                )}

                <div>
                  <label className={styles.mobileFieldLabel}>Email address</label>
                  <input
                    type="email"
                    className={styles.mobileInput}
                    placeholder="you@email.com"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    required
                  />
                </div>

                <div>
                  <label className={styles.mobileFieldLabel}>Password</label>
                  <div className={styles.mobilePasswordWrapper}>
                    <input
                      type={showPassword ? 'text' : 'password'}
                      className={`${styles.mobileInput} ${isLoginMode ? styles.mobilePasswordInput : ''}`}
                      placeholder="••••••••"
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      required
                    />
                    {isLoginMode && (
                      <button
                        type="button"
                        className={styles.mobileForgotPill}
                        onClick={() => setError('Demo mode: password reset is not enabled.')}
                      >
                        I forgot
                      </button>
                    )}
                  </div>
                </div>

                {!isLoginMode && (
                  <div>
                    <label className={styles.mobileFieldLabel}>Confirm password</label>
                    <input
                      type={showPassword ? 'text' : 'password'}
                      className={styles.mobileInput}
                      placeholder="••••••••"
                      value={confirmPassword}
                      onChange={(e) => setConfirmPassword(e.target.value)}
                    />
                  </div>
                )}

                {error && (
                  <div className={styles.mobileError}>
                    <p className={styles.mobileErrorText}>{error}</p>
                  </div>
                )}

                <button type="submit" className={styles.mobileSubmit} disabled={isLoading}>
                  {isLoading ? (isLoginMode ? 'Logging in...' : 'Creating account...') : isLoginMode ? 'Log in' : 'Create account'}
                </button>

                <div className={styles.mobileDivider}>
                  <div className={styles.mobileDividerLine} />
                  <span className={styles.mobileDividerText}>or continue with</span>
                  <div className={styles.mobileDividerLine} />
                </div>

                <button type="button" className={styles.mobileGoogle} onClick={handleGoogleSignIn} disabled={isLoading}>
                  <svg width="18" height="18" viewBox="0 0 24 24">
                    <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" />
                    <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" />
                    <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" />
                    <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" />
                  </svg>
                  Continue with Google
                </button>

                <div className={styles.mobileSwitch}>
                  <span className={styles.mobileSwitchText}>
                    {isLoginMode ? "Don't have an account? " : 'Already have an account? '}
                  </span>
                  <button type="button" className={styles.mobileSwitchLink} onClick={toggleMode} disabled={isLoading}>
                    {isLoginMode ? 'Sign up' : 'Log in'}
                  </button>
                </div>
              </>
            )}
          </form>
        </div>
      </div>
    </>
  );
}
