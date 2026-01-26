'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import styles from './RaimonShell.module.css';
import { Home, Folder, Plus, LogOut, ChevronLeft, Menu, X } from 'lucide-react';

export default function RaimonShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const flush = pathname?.startsWith('/dashboard/focus');
  const [collapsed, setCollapsed] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);

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

  function isActive(href: string) {
    if (!pathname) return false;
    if (pathname === href) return true;
    if (href === '/') return false;
    // Only match child routes (href + '/'), and exclude /projects/new from matching /projects
    if (href === '/projects' && pathname.startsWith('/projects/new')) return false;
    return pathname.startsWith(href + '/');
  }

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
          <button className={styles.headerLogout} type="button">
            <LogOut />
            <span>Log out</span>
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
