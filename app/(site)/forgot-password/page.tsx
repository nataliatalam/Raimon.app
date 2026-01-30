'use client';

import { useState } from 'react';
import type { FormEvent } from 'react';
import Link from 'next/link';
import Image from 'next/image';
import { useRouter } from 'next/navigation';
import styles from '../login/login.module.css';
import { apiFetch } from '../../../lib/api-client';
import type { ApiSuccessResponse } from '../../../types/api';

export default function ForgotPasswordPage() {
  const router = useRouter();
  const [email, setEmail] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError('');

    if (!email.trim()) {
      setError('Please enter your email address');
      return;
    }

    setIsLoading(true);

    try {
      await apiFetch<ApiSuccessResponse<void>>('/api/auth/forgot-password', {
        method: 'POST',
        body: { email: email.trim() },
        skipAuth: true,
      });

      setSuccess(true);
    } catch (err: any) {
      // Always show success to prevent email enumeration
      setSuccess(true);
    } finally {
      setIsLoading(false);
    }
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
                  <span className={styles.pillText}>Secure password reset</span>
                </div>

                <h1 className={styles.heroTitle}>
                  Reset your
                  <br />
                  <span className={styles.heroGradient}>password</span>
                </h1>
              </div>

              <div className={styles.formCard}>
                <h2 className={styles.formTitle}>Forgot password</h2>

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
                        Check your email
                      </p>
                      <p style={{ color: 'rgba(255,255,255,0.7)', fontSize: '14px' }}>
                        If an account exists for <strong>{email}</strong>, you will receive a
                        password reset link shortly.
                      </p>
                    </div>

                    <button
                      type="button"
                      className={styles.submitBtn}
                      onClick={() => router.push('/login')}
                      style={{ marginTop: '20px' }}
                    >
                      Back to login
                    </button>
                  </div>
                ) : (
                  <form onSubmit={handleSubmit} className={styles.formContent}>
                    <p style={{ color: 'rgba(255,255,255,0.6)', fontSize: '14px', marginBottom: '16px' }}>
                      Enter your email address and we'll send you a link to reset your password.
                    </p>

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

                    {error && (
                      <div className={styles.errorBox}>
                        <p className={styles.errorText}>{error}</p>
                      </div>
                    )}

                    <button type="submit" className={styles.submitBtn} disabled={isLoading}>
                      {isLoading ? 'Sending...' : 'Send reset link'}
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
            Reset your
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
                  Check your email
                </p>
                <p style={{ color: 'rgba(255,255,255,0.7)', fontSize: '14px' }}>
                  If an account exists for <strong>{email}</strong>, you will receive a password
                  reset link shortly.
                </p>
              </div>

              <button
                type="button"
                className={styles.mobileSubmit}
                onClick={() => router.push('/login')}
                style={{ marginTop: '20px' }}
              >
                Back to login
              </button>
            </div>
          ) : (
            <form className={styles.mobileForm} onSubmit={handleSubmit}>
              <p style={{ color: 'rgba(255,255,255,0.6)', fontSize: '14px', marginBottom: '16px' }}>
                Enter your email and we'll send you a reset link.
              </p>

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

              {error && (
                <div className={styles.mobileError}>
                  <p className={styles.mobileErrorText}>{error}</p>
                </div>
              )}

              <button type="submit" className={styles.mobileSubmit} disabled={isLoading}>
                {isLoading ? 'Sending...' : 'Send reset link'}
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
