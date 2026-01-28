'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import styles from './RaimonShell.module.css';
import { Home, Folder, Plus, LogOut, ChevronLeft, Menu, X } from 'lucide-react';
import { useSession } from './providers/SessionProvider';
import { apiFetch } from '../../lib/api-client';

export default function RaimonShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const { session, status, clear } = useSession();
  const flush = pathname?.startsWith('/dashboard/focus');
  const [collapsed, setCollapsed] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const [logoutPending, setLogoutPending] = useState(false);

  const isMobile = () => (typeof window !== 'undefined' ? window.innerWidth <= 768 : false);

  // Restore collapsed state (desktop only)
  useEffect(() => {
    if (isMobile()) return;
    const saved = localStorage.getItem('raimon_sidebar_collapsed');
    if (saved === 'true') setCollapsed(true);
  }, []);

  // Lock body scroll when mobile menu open
  useEffect(() => {
    if (!isMobile()) return;
    document.body.style.overflow = mobileOpen ? 'hidden' : '';
    return () => {
      document.body.style.overflow = '';
    };
  }, [mobileOpen]);

  function toggleCollapsed() {
    setCollapsed((v) => {
      const next = !v;
      localStorage.setItem('raimon_sidebar_collapsed', String(next));
      return next;
    });
  }

  useEffect(() => {
    if (status === 'ready' && !session.accessToken) {
      router.replace('/login');
    }
  }, [status, session.accessToken, router]);

  function isActive(href: string) {
    if (!pathname) return false;
    if (pathname === href) return true;
    if (href === '/') return false;
    // Only match child routes (href + '/'), and exclude /projects/new from matching /projects
    if (href === '/projects' && pathname.startsWith('/projects/new')) return false;
    return pathname.startsWith(href + '/');
  }

  async function handleLogout() {
    if (logoutPending) return;
    setLogoutPending(true);
    try {
      await apiFetch('/api/auth/logout', { method: 'POST' });
    } catch {
      // ignore network errors
    } finally {
      clear();
      setLogoutPending(false);
      router.replace('/login');
    }
  }

  if (status === 'loading') {
    return <div className={styles.shellLoading}>Loading workspace…</div>;
  }

  if (!session.accessToken) {
    return <div className={styles.shellLoading}>Redirecting…</div>;
  }

  const userName = session.user?.name ?? 'Friend';

  return (
    <div className={styles.app}>
      {/* Mobile menu button */}
      <button
        className={styles.mobileMenuBtn}
        onClick={() => setMobileOpen(true)}
        aria-label="Open menu"
        type="button"
      >
        <Menu />
      </button>

      {/* Mobile overlay */}
      <div
        className={`${styles.mobileOverlay} ${mobileOpen ? styles.mobileOverlayActive : ''}`}
        onClick={() => setMobileOpen(false)}
      />

      {/* Sidebar */}
      <aside
        className={[
          styles.sidebar,
          collapsed ? styles.sidebarCollapsed : '',
          mobileOpen ? styles.sidebarMobileOpen : '',
        ].join(' ')}
      >
        <button
          className={styles.mobileCloseBtn}
          onClick={() => setMobileOpen(false)}
          aria-label="Close menu"
          type="button"
        >
          <X />
        </button>

        {/* LOGO */}
        <div className={styles.logoContainer}>
          <div className={styles.logoWrapper}>
            <img src="/raimon-logo.png" alt="Raimon" className={styles.logoImg} />
          </div>
        </div>

        <nav className={styles.nav}>
          <Link
            href="/dashboard"
            className={`${styles.navItem} ${isActive('/dashboard') ? styles.navItemActive : ''}`}
            data-tooltip="Home"
            onClick={() => setMobileOpen(false)}
          >
            <Home />
            <span>Home</span>
          </Link>

          <Link
            href="/projects/new"
            className={`${styles.navItem} ${isActive('/projects/new') ? styles.navItemActive : ''}`}
            data-tooltip="Add Project"
            onClick={() => setMobileOpen(false)}
          >
            <Plus />
            <span>Add Project</span>
          </Link>

          <Link
            href="/projects"
            className={`${styles.navItem} ${isActive('/projects') ? styles.navItemActive : ''}`}
            data-tooltip="My Projects"
            onClick={() => setMobileOpen(false)}
          >
            <Folder />
            <span>My Projects</span>
          </Link>

          {/* Desktop collapse toggle */}
          <button
            className={styles.sidebarToggle}
            onClick={toggleCollapsed}
            title="Toggle sidebar"
            aria-label="Toggle sidebar"
            type="button"
          >
            <ChevronLeft className={collapsed ? styles.chevRot : ''} />
          </button>
        </nav>
      </aside>

      {/* Main */}
      <div className={`${styles.mainContent} ${collapsed ? styles.mainCollapsed : ''}`}>
        <header className={styles.header}>
          <div className={styles.headerUser}>
            <span className={styles.headerGreeting}>Welcome back, {userName}</span>
          </div>
          <button className={styles.headerLogout} onClick={handleLogout} type="button" disabled={logoutPending}>
            <LogOut />
            <span>{logoutPending ? 'Logging out…' : 'Log out'}</span>
          </button>
        </header>

        <div className={styles.contentArea}>
          <div className={styles.contentInner}>
            <div className={`${styles.contentScroll} ${flush ? styles.contentScrollFlush : ''}`}>
              {children}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
