'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import styles from './RaimonShell.module.css';
import { Home, Folder, Plus, LogOut, ChevronLeft, Menu, X } from 'lucide-react';
import { useSession } from './providers/SessionProvider';
import { createClient } from '@supabase/supabase-js';
// import { apiFetch } from '../../lib/api-client'; // opcional, si todavía lo usas

const SUPABASE_URL = process.env.NEXT_PUBLIC_SUPABASE_URL;
const SUPABASE_ANON = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;

if (!SUPABASE_URL || !SUPABASE_ANON) {
  throw new Error('Missing NEXT_PUBLIC_SUPABASE_URL or NEXT_PUBLIC_SUPABASE_ANON_KEY');
}

const supabase = createClient(SUPABASE_URL, SUPABASE_ANON, {
  auth: {
    persistSession: true,
    autoRefreshToken: true,
    detectSessionInUrl: true,
    flowType: 'pkce',
  },
});

export default function RaimonShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const { session, status, clear } = useSession();
  const flush = pathname?.startsWith('/dashboard/focus');

  const [collapsed, setCollapsed] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const [logoutPending, setLogoutPending] = useState(false);

  const isMobile = () => (typeof window !== 'undefined' ? window.innerWidth <= 768 : false);

  useEffect(() => {
    if (isMobile()) return;
    const saved = localStorage.getItem('raimon_sidebar_collapsed');
    if (saved === 'true') setCollapsed(true);
  }, []);

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
    if (href === '/projects' && pathname.startsWith('/projects/new')) return false;
    return pathname.startsWith(href + '/');
  }

  async function handleLogout() {
    if (logoutPending) return;
    setLogoutPending(true);

    try {
      // ✅ REAL logout from Supabase (clears persisted session)
      await supabase.auth.signOut({ scope: 'local' });

      // (Opcional) Si todavía tienes backend cookies/sessions:
      // await apiFetch('/api/auth/logout', { method: 'POST' });
    } catch (e) {
      // aunque falle, igual limpia tu state para sacar a la persona
      console.error('Logout error:', e);
    } finally {
      clear(); // ✅ limpia SessionProvider
      setLogoutPending(false);
      router.replace('/login');
      router.refresh();
    }
  }

  if (status === 'loading') {
    return <div className={styles.shellLoading}>Loading workspace…</div>;
  }

  if (!session.accessToken) {
    return <div className={styles.shellLoading}>Redirecting…</div>;
  }

  const userName = (session.user as any)?.name ?? (session.user as any)?.user_metadata?.full_name ?? 'Friend';

  return (
    <div className={styles.app}>
      <button
        className={styles.mobileMenuBtn}
        onClick={() => setMobileOpen(true)}
        aria-label="Open menu"
        type="button"
      >
        <Menu />
      </button>

      <div
        className={`${styles.mobileOverlay} ${mobileOpen ? styles.mobileOverlayActive : ''}`}
        onClick={() => setMobileOpen(false)}
      />

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

      <div className={`${styles.mainContent} ${collapsed ? styles.mainCollapsed : ''}`}>
        <header className={styles.header}>
          <div className={styles.headerUser}>
            <span className={styles.headerGreeting}>Welcome back, {userName}</span>
          </div>

          <button
            className={styles.headerLogout}
            onClick={handleLogout}
            type="button"
            disabled={logoutPending}
          >
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
