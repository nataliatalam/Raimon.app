'use client';

import { useState, useEffect } from 'react';
import type { FormEvent } from 'react';
import Link from 'next/link';
import Image from 'next/image';
import { useRouter } from 'next/navigation';
import styles from './login.module.css';
import { useSession } from '../../components/providers/SessionProvider';
import { apiFetch, ApiError } from '../../../lib/api-client';
import { createClient } from '../../../lib/supabase/client';
import type { ApiSuccessResponse } from '../../../types/api';

type Step = 'auth' | 'verify';

type OnboardingStatusResponse = ApiSuccessResponse<{
  onboarding_completed?: boolean;
  onboarding_step?: number;
}>;

function hasCompletedOnboarding(user: any) {
  return !!user?.onboarding_completed || !!user?.user_metadata?.onboarding_completed;
}

// Password requirements checker
const PasswordRequirements = ({ password }: { password: string }) => {
  const requirements = [
    { label: 'At least 8 characters', met: password.length >= 8 },
    { label: 'Contains uppercase letter', met: /[A-Z]/.test(password) },
    { label: 'Contains lowercase letter', met: /[a-z]/.test(password) },
    { label: 'Contains a number', met: /\d/.test(password) },
  ];

  return (
    <div
      style={{
        marginTop: '8px',
        padding: '12px',
        background: 'rgba(255,255,255,0.03)',
        borderRadius: '8px',
        fontSize: '13px',
      }}
    >
      <div style={{ color: 'rgba(255,255,255,0.5)', marginBottom: '8px', fontWeight: 500 }}>
        Password requirements:
      </div>
      {requirements.map((req, i) => (
        <div
          key={i}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            marginBottom: '4px',
            color: req.met ? '#4ade80' : 'rgba(255,255,255,0.4)',
            transition: 'color 0.2s',
          }}
        >
          <span style={{ fontSize: '14px' }}>{req.met ? '✓' : '○'}</span>
          <span>{req.label}</span>
        </div>
      ))}
    </div>
  );
};

function normalizeAuthErrorMessage(msg?: string) {
  return (msg ?? '').toLowerCase();
}

export default function LoginPage() {
  const router = useRouter();
  const { session, status, setSession, clear } = useSession();
  const supabase = createClient();

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

  // ✅ redirect if already authed
  useEffect(() => {
    if (status !== 'ready') return;
    if (!session.accessToken) return;

    let canceled = false;

    (async () => {
      const fallback = hasCompletedOnboarding(session.user);
      const statusResponse = await fetchOnboardingStatus(fallback);
      if (canceled || !statusResponse) return;
      router.replace(statusResponse.completed ? '/dashboard' : '/onboarding-questions');
    })();

    return () => {
      canceled = true;
    };
  }, [status, session.accessToken, session.user, router]);

  const toggleMode = () => {
    setError('');
    setStep('auth');
    setVerificationCode('');
    setPendingEmail('');
    setIsLoginMode((v) => !v);
  };

  const togglePassword = () => setShowPassword((v) => !v);

  function goDashboard() {
    window.location.href = '/dashboard';
  }

  function goOnboarding() {
    window.location.href = '/onboarding-questions';
  }

  async function fetchOnboardingStatus(fallbackCompleted: boolean) {
    try {
      const response = await apiFetch<OnboardingStatusResponse>('/api/users/onboarding-status');
      return {
        completed: !!response.data?.onboarding_completed,
        step: response.data?.onboarding_step ?? 0,
      };
    } catch (err) {
      if (err instanceof ApiError && err.status === 401) {
        clear();
        return null;
      }
      console.warn('Failed to fetch onboarding status', err);
      return { completed: fallbackCompleted, step: fallbackCompleted ? 6 : 0 };
    }
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError('');

    // Basic validation
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

      // Validate password requirements
      const passwordErrors: string[] = [];
      if (password.length < 8) passwordErrors.push('At least 8 characters');
      if (!/[A-Z]/.test(password)) passwordErrors.push('One uppercase letter');
      if (!/[a-z]/.test(password)) passwordErrors.push('One lowercase letter');
      if (!/\d/.test(password)) passwordErrors.push('One number');
      if (passwordErrors.length > 0) {
        setError('Password needs: ' + passwordErrors.join(', '));
        return;
      }
    }

    setIsLoading(true);

    try {
      if (isLoginMode) {
        // ✅ Email + password login via backend API (JWT)
        const result = await apiFetch<ApiSuccessResponse<{
          user: any;
          token: string;
          refresh_token: string;
        }>>('/api/auth/login', {
          method: 'POST',
          body: { email: email.trim(), password: password.trim() },
          skipAuth: true,
        });

        if (!result.success || !result.data?.token) {
          setError('Login failed: no token returned.');
          return;
        }

        setSession({
          accessToken: result.data.token,
          refreshToken: result.data.refresh_token ?? '',
          user: result.data.user ?? null,
        });

        const onboardingCompleted = result.data.user?.onboarding_completed;
        if (onboardingCompleted) goDashboard();
        else goOnboarding();
      } else {
        // ✅ SIGNUP via backend API (JWT)
        try {
          const result = await apiFetch<ApiSuccessResponse<{
            user: any;
            token: string;
            refresh_token: string;
          }>>('/api/auth/signup', {
            method: 'POST',
            body: {
              email: email.trim(),
              password: password.trim(),
              name: name.trim(),
            },
            skipAuth: true,
          });

          if (!result.success || !result.data?.token) {
            setError('Signup failed: no token returned.');
            return;
          }

          setSession({
            accessToken: result.data.token,
            refreshToken: result.data.refresh_token ?? '',
            user: result.data.user ?? null,
          });

          goOnboarding();
        } catch (err: any) {
          const m = normalizeAuthErrorMessage(err?.message || '');
          if (
            m.includes('already registered') ||
            m.includes('user already') ||
            m.includes('already exists')
          ) {
            setError('This email already has an account. Please log in instead.');
            return;
          }
          throw err;
        }
      }
    } catch (err: any) {
      setError(err?.message ?? 'Something went wrong. Please try again.');
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
    const code = verificationCode.trim();
    if (!code || code.length < 6) {
      setError('Enter the 6-digit code from your email.');
      return;
    }

    setIsLoading(true);
    try {
      // ✅ Verify OTP via backend API
      await apiFetch<ApiSuccessResponse<void>>('/api/auth/verify-code', {
        method: 'POST',
        body: { email: pendingEmail, code },
        skipAuth: true,
      });

      // ✅ After verification, login to get JWT tokens
      const loginResult = await apiFetch<ApiSuccessResponse<{
        user: any;
        token: string;
        refresh_token: string;
      }>>('/api/auth/login', {
        method: 'POST',
        body: { email: pendingEmail, password: password.trim() },
        skipAuth: true,
      });

      if (!loginResult.success || !loginResult.data?.token) {
        setError('Verification succeeded but login failed.');
        return;
      }

      setSession({
        accessToken: loginResult.data.token,
        refreshToken: loginResult.data.refresh_token ?? '',
        user: loginResult.data.user ?? null,
      });

      goOnboarding();
    } catch (err: any) {
      setError(err?.message ?? 'Invalid code. Try again.');
    } finally {
      setIsLoading(false);
    }
  }

  async function handleResendCode() {
    setError('');
    if (!pendingEmail) return;

    setIsLoading(true);
    try {
      // ✅ Resend signup OTP
      // supabase-js v2: resend({ type:'signup', email })
      const anyAuth: any = supabase.auth as any;

      if (typeof anyAuth.resend === 'function') {
        const { error: resendErr } = await anyAuth.resend({
          type: 'signup',
          email: pendingEmail,
        });
        if (resendErr) throw resendErr;
      } else {
        // Fallback (viejo): signInWithOtp puede reenviar, pero puede intentar “login magic”.
        // En tu caso funciona como resend si el provider está en OTP.
        const { error: resendErr } = await supabase.auth.signInWithOtp({
          email: pendingEmail,
          options: { shouldCreateUser: false },
        });
        if (resendErr) throw resendErr;
      }

      setError('Code resent. Check your email.');
    } catch (err: any) {
      setError(err?.message ?? 'Could not resend code.');
    } finally {
      setIsLoading(false);
    }
  }

  async function handleGoogleSignIn() {
    setError('');
    setIsLoading(true);

    try {
      const { data, error: gErr } = await supabase.auth.signInWithOAuth({
        provider: 'google',
        options: {
          redirectTo: `${window.location.origin}/auth/callback`,
          queryParams: {
            prompt: 'consent',
            access_type: 'offline',
          },
        },
      });

      if (gErr) throw gErr;

      // ✅ fuerza navegación si Supabase devuelve URL
      if (data?.url) {
        window.location.assign(data.url);
      }
      // si no hay url, supabase-js puede redirigir solo
    } catch (err: any) {
      setError(err?.message ?? 'Google sign-in failed.');
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
                          placeholder="Enter 6-digit code"
                          value={verificationCode}
                          onChange={(e) =>
                            setVerificationCode(e.target.value.replace(/[^\d]/g, '').slice(0, 6))
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
                        {!isLoginMode && <PasswordRequirements password={password} />}
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

                          <button
                            type="button"
                            className={styles.forgotLink}
                            onClick={() => setError('Password reset not wired yet.')}
                          >
                            Forgot password?
                          </button>
                        </div>
                      )}

                      <button type="submit" className={styles.submitBtn} disabled={isLoading}>
                        {isLoading
                          ? isLoginMode
                            ? 'Logging in...'
                            : 'Sending code...'
                          : isLoginMode
                          ? 'Log in'
                          : 'Send 6-digit code'}
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
                    placeholder="Enter 6-digit code"
                    value={verificationCode}
                    onChange={(e) =>
                      setVerificationCode(e.target.value.replace(/[^\d]/g, '').slice(0, 6))
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
                      className={`${styles.mobileInput} ${styles.mobilePasswordInput}`}
                      placeholder="••••••••"
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      required
                    />
                    <button
                      type="button"
                      className={styles.mobilePasswordToggle}
                      onClick={togglePassword}
                      style={isLoginMode ? { right: '100px' } : undefined}
                    >
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
                    {isLoginMode && (
                      <button
                        type="button"
                        className={styles.mobileForgotPill}
                        onClick={() => setError('Password reset not wired yet.')}
                      >
                        I forgot
                      </button>
                    )}
                  </div>
                  {!isLoginMode && <PasswordRequirements password={password} />}
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
                  {isLoading
                    ? isLoginMode
                      ? 'Logging in...'
                      : 'Sending code...'
                    : isLoginMode
                    ? 'Log in'
                    : 'Send 6-digit code'}
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
