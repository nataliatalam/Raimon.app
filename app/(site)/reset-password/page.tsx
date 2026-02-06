'use client';

import { useState, useEffect , Suspense } from 'react';
import type { FormEvent } from 'react';
import Link from 'next/link';
import Image from 'next/image';
import { useRouter, useSearchParams } from 'next/navigation';
import styles from '../login/login.module.css';
import { apiFetch } from '../../../lib/api-client';
import { createClient } from '../../../lib/supabase/client';
import type { ApiSuccessResponse } from '../../../types/api';

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

function ResetPasswordContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const supabase = createClient();

  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);
  const [accessToken, setAccessToken] = useState<string | null>(null);
  const [isValidating, setIsValidating] = useState(true);

  // Extract token from URL hash or query params on mount
  useEffect(() => {
    const extractToken = async () => {
      setIsValidating(true);

      // Check URL hash for Supabase redirect tokens
      if (typeof window !== 'undefined') {
        const hash = window.location.hash;
        if (hash) {
          const params = new URLSearchParams(hash.substring(1));
          const token = params.get('access_token');
          const type = params.get('type');

          if (token && type === 'recovery') {
            setAccessToken(token);
            setIsValidating(false);
            return;
          }
        }

        // Also check for code in query params (PKCE flow)
        const code = searchParams.get('code');
        if (code) {
          try {
            // Exchange the code for a session
            const { data, error } = await supabase.auth.exchangeCodeForSession(code);
            if (!error && data.session?.access_token) {
              setAccessToken(data.session.access_token);
              setIsValidating(false);
              return;
            }
          } catch (err) {
            console.error('Failed to exchange code:', err);
          }
        }

        // Check if user has an active session from recovery
        const { data: { session } } = await supabase.auth.getSession();
        if (session?.access_token) {
          setAccessToken(session.access_token);
          setIsValidating(false);
          return;
        }
      }

      setIsValidating(false);
      setError('Invalid or expired reset link. Please request a new one.');
    };

    extractToken();
  }, [searchParams, supabase]);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError('');

    if (!accessToken) {
      setError('Invalid reset token. Please request a new reset link.');
      return;
    }

    if (!password.trim()) {
      setError('Please enter a new password');
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

    setIsLoading(true);

    try {
      await apiFetch<ApiSuccessResponse<void>>('/api/auth/reset-password', {
        method: 'POST',
        body: { token: accessToken, password: password.trim() },
        skipAuth: true,
      });

      setSuccess(true);

      // Sign out from Supabase to clear the recovery session
      await supabase.auth.signOut();
    } catch (err: any) {
      setError(err?.message ?? 'Failed to reset password. Please try again.');
    } finally {
      setIsLoading(false);
    }
  }

  const togglePassword = () => setShowPassword((v) => !v);

  if (isValidating) {
    return (
      <div
        style={{
          minHeight: '100vh',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          background: '#0a0a0a',
          color: 'white',
        }}
      >
        <p>Validating reset link...</p>
      </div>
    );
  }

  return (
    <>
      {/* Desktop Version */}
      <div className={styles.desktopContainer}>
        <div className={styles.mainContainer}>
          <div className={styles.aurora} />

          <div className={styles.header}>
            <div className={styles.navDesktop}>
              <div className={styles.navRight}>
                <span className={styles.navText}>Remember your password?</span>
                <button
                  className={styles.navBtn}
                  onClick={() => router.push('/login')}
                  type="button"
                >
                  Log in
                </button>
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
                  <span className={styles.pillText}>Create a new password</span>
                </div>

                <h1 className={styles.heroTitle}>
                  New
                  <br />
                  <span className={styles.heroGradient}>password</span>
                </h1>
              </div>

              <div className={styles.formCard}>
                <h2 className={styles.formTitle}>Reset password</h2>

                {success ? (
                  <div className={styles.formContent}>
                    <div
                      style={{
                        padding: '20px',
                        background: 'rgba(74, 222, 128, 0.1)',
                        borderRadius: '12px',
                        border: '1px solid rgba(74, 222, 128, 0.2)',
                      }}
                    >
                      <p style={{ color: '#4ade80', marginBottom: '12px', fontWeight: 500 }}>
                        Password reset successful!
                      </p>
                      <p style={{ color: 'rgba(255,255,255,0.7)', fontSize: '14px' }}>
                        Your password has been updated. You can now log in with your new password.
                      </p>
                    </div>

                    <button
                      type="button"
                      className={styles.submitBtn}
                      onClick={() => router.push('/login')}
                      style={{ marginTop: '20px' }}
                    >
                      Go to login
                    </button>
                  </div>
                ) : !accessToken ? (
                  <div className={styles.formContent}>
                    <div
                      style={{
                        padding: '20px',
                        background: 'rgba(239, 68, 68, 0.1)',
                        borderRadius: '12px',
                        border: '1px solid rgba(239, 68, 68, 0.2)',
                      }}
                    >
                      <p style={{ color: '#ef4444', marginBottom: '12px', fontWeight: 500 }}>
                        Invalid reset link
                      </p>
                      <p style={{ color: 'rgba(255,255,255,0.7)', fontSize: '14px' }}>
                        This password reset link is invalid or has expired. Please request a new
                        one.
                      </p>
                    </div>

                    <button
                      type="button"
                      className={styles.submitBtn}
                      onClick={() => router.push('/forgot-password')}
                      style={{ marginTop: '20px' }}
                    >
                      Request new link
                    </button>
                  </div>
                ) : (
                  <form onSubmit={handleSubmit} className={styles.formContent}>
                    <p
                      style={{
                        color: 'rgba(255,255,255,0.6)',
                        fontSize: '14px',
                        marginBottom: '16px',
                      }}
                    >
                      Enter your new password below.
                    </p>

                    <div>
                      <label className={styles.formLabel}>New password</label>
                      <div className={styles.passwordWrapper}>
                        <input
                          type={showPassword ? 'text' : 'password'}
                          className={`${styles.formInput} ${styles.passwordInput}`}
                          placeholder="Enter new password"
                          value={password}
                          onChange={(e) => setPassword(e.target.value)}
                          required
                        />
                        <button
                          type="button"
                          className={styles.passwordToggle}
                          onClick={togglePassword}
                        >
                          {showPassword ? (
                            <svg
                              width="20"
                              height="20"
                              viewBox="0 0 24 24"
                              fill="none"
                              stroke="currentColor"
                              strokeWidth="2"
                            >
                              <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24" />
                              <line x1="1" y1="1" x2="23" y2="23" />
                            </svg>
                          ) : (
                            <svg
                              width="20"
                              height="20"
                              viewBox="0 0 24 24"
                              fill="none"
                              stroke="currentColor"
                              strokeWidth="2"
                            >
                              <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
                              <circle cx="12" cy="12" r="3" />
                            </svg>
                          )}
                        </button>
                      </div>
                      <PasswordRequirements password={password} />
                    </div>

                    <div>
                      <label className={styles.formLabel}>Confirm new password</label>
                      <input
                        type={showPassword ? 'text' : 'password'}
                        className={styles.formInput}
                        placeholder="Confirm new password"
                        value={confirmPassword}
                        onChange={(e) => setConfirmPassword(e.target.value)}
                        required
                      />
                    </div>

                    {error && (
                      <div className={styles.errorBox}>
                        <p className={styles.errorText}>{error}</p>
                      </div>
                    )}

                    <button type="submit" className={styles.submitBtn} disabled={isLoading}>
                      {isLoading ? 'Resetting...' : 'Reset password'}
                    </button>

                    <div className={styles.bottomSignup}>
                      <span className={styles.bottomSignupText}>Remember your password? </span>
                      <button
                        type="button"
                        className={styles.bottomSignupLink}
                        onClick={() => router.push('/login')}
                      >
                        Log in
                      </button>
                    </div>
                  </form>
                )}
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
            New
            <br />
            <span className={styles.mobileTitleGradient}>password</span>
          </h1>
        </div>

        <div className={styles.mobileCard}>
          {success ? (
            <div className={styles.mobileForm}>
              <div
                style={{
                  padding: '20px',
                  background: 'rgba(74, 222, 128, 0.1)',
                  borderRadius: '12px',
                  border: '1px solid rgba(74, 222, 128, 0.2)',
                }}
              >
                <p style={{ color: '#4ade80', marginBottom: '12px', fontWeight: 500 }}>
                  Password reset successful!
                </p>
                <p style={{ color: 'rgba(255,255,255,0.7)', fontSize: '14px' }}>
                  You can now log in with your new password.
                </p>
              </div>

              <button
                type="button"
                className={styles.mobileSubmit}
                onClick={() => router.push('/login')}
                style={{ marginTop: '20px' }}
              >
                Go to login
              </button>
            </div>
          ) : !accessToken ? (
            <div className={styles.mobileForm}>
              <div
                style={{
                  padding: '20px',
                  background: 'rgba(239, 68, 68, 0.1)',
                  borderRadius: '12px',
                  border: '1px solid rgba(239, 68, 68, 0.2)',
                }}
              >
                <p style={{ color: '#ef4444', marginBottom: '12px', fontWeight: 500 }}>
                  Invalid reset link
                </p>
                <p style={{ color: 'rgba(255,255,255,0.7)', fontSize: '14px' }}>
                  This link is invalid or expired.
                </p>
              </div>

              <button
                type="button"
                className={styles.mobileSubmit}
                onClick={() => router.push('/forgot-password')}
                style={{ marginTop: '20px' }}
              >
                Request new link
              </button>
            </div>
          ) : (
            <form className={styles.mobileForm} onSubmit={handleSubmit}>
              <p
                style={{ color: 'rgba(255,255,255,0.6)', fontSize: '14px', marginBottom: '16px' }}
              >
                Enter your new password below.
              </p>

              <div>
                <label className={styles.mobileFieldLabel}>New password</label>
                <div className={styles.mobilePasswordWrapper}>
                  <input
                    type={showPassword ? 'text' : 'password'}
                    className={`${styles.mobileInput} ${styles.mobilePasswordInput}`}
                    placeholder="Enter new password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                  />
                  <button
                    type="button"
                    className={styles.mobilePasswordToggle}
                    onClick={togglePassword}
                  >
                    {showPassword ? (
                      <svg
                        width="20"
                        height="20"
                        viewBox="0 0 24 24"
                        fill="none"
                        stroke="currentColor"
                        strokeWidth="2"
                      >
                        <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94" />
                        <line x1="1" y1="1" x2="23" y2="23" />
                      </svg>
                    ) : (
                      <svg
                        width="20"
                        height="20"
                        viewBox="0 0 24 24"
                        fill="none"
                        stroke="currentColor"
                        strokeWidth="2"
                      >
                        <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
                        <circle cx="12" cy="12" r="3" />
                      </svg>
                    )}
                  </button>
                </div>
                <PasswordRequirements password={password} />
              </div>

              <div>
                <label className={styles.mobileFieldLabel}>Confirm password</label>
                <input
                  type={showPassword ? 'text' : 'password'}
                  className={styles.mobileInput}
                  placeholder="Confirm new password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  required
                />
              </div>

              {error && (
                <div className={styles.mobileError}>
                  <p className={styles.mobileErrorText}>{error}</p>
                </div>
              )}

              <button type="submit" className={styles.mobileSubmit} disabled={isLoading}>
                {isLoading ? 'Resetting...' : 'Reset password'}
              </button>

              <div className={styles.mobileSwitch}>
                <span className={styles.mobileSwitchText}>Remember your password? </span>
                <button
                  type="button"
                  className={styles.mobileSwitchLink}
                  onClick={() => router.push('/login')}
                >
                  Log in
                </button>
              </div>
            </form>
          )}
        </div>
      </div>
    </>
  );
}

export default function ResetPasswordPage() {
  return (
    <Suspense
      fallback={
        <div
          style={{
            minHeight: '100vh',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            background: '#0a0a0a',
            color: 'white',
          }}
        >
          <p>Loading...</p>
        </div>
      }
    >
      <ResetPasswordContent />
    </Suspense>
  );
}