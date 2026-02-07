'use client';

import React, { useState, useEffect } from 'react';
import styles from './SettingsPage.module.css';
import { apiFetch } from '../../lib/api-client';

type Props = {
  onRetakeOnboarding?: (resetData: boolean) => void;
  onExport?: (type: string) => void;
};

type CalendarStatus = {
  connected: boolean;
  status: string;
  last_synced_at?: string;
  events_synced?: number;
};

export default function SettingsPage({ onRetakeOnboarding, onExport }: Props) {
  const [notificationsEnabled, setNotificationsEnabled] = useState(true);
  const [resetData, setResetData] = useState(false);
  const [calendarStatus, setCalendarStatus] = useState<CalendarStatus | null>(null);
  const [calendarLoading, setCalendarLoading] = useState(false);
  const [syncLoading, setSyncLoading] = useState(false);

  useEffect(() => {
    fetchCalendarStatus();
  }, []);

  const fetchCalendarStatus = async () => {
    try {
      const response = await apiFetch<{ success: boolean; data: CalendarStatus }>('/api/calendar/status');
      if (response.success) {
        setCalendarStatus(response.data);
      }
    } catch (error) {
      console.error('Failed to fetch calendar status:', error);
    }
  };

  const handleConnectCalendar = async () => {
    setCalendarLoading(true);
    try {
      const response = await apiFetch<{ success: boolean; data: { authorization_url: string } }>('/api/calendar/auth/url');
      console.log('Calendar auth response:', response);
      if (response.success && response.data.authorization_url) {
        window.location.href = response.data.authorization_url;
      } else {
        alert('Failed to get authorization URL from server.');
      }
    } catch (error: unknown) {
      console.error('Failed to get calendar auth URL:', error);
      const errorMessage = error instanceof Error ? error.message : 'Unknown error';
      alert(`Failed to connect to Google Calendar: ${errorMessage}`);
    } finally {
      setCalendarLoading(false);
    }
  };

  const handleSyncCalendar = async () => {
    setSyncLoading(true);
    try {
      const response = await apiFetch<{ success: boolean; data: { events_synced: number } }>('/api/calendar/sync', {
        method: 'POST',
        body: { full_sync: false, days_back: 30, days_forward: 90 },
      });
      if (response.success) {
        alert(`Synced ${response.data.events_synced} events from your calendar!`);
        fetchCalendarStatus();
      }
    } catch (error) {
      console.error('Failed to sync calendar:', error);
      alert('Failed to sync calendar. Please try again.');
    } finally {
      setSyncLoading(false);
    }
  };

  const handleDisconnectCalendar = async () => {
    if (!confirm('Are you sure you want to disconnect Google Calendar? This will remove all synced events.')) {
      return;
    }
    try {
      await apiFetch('/api/calendar/disconnect', { method: 'DELETE' });
      setCalendarStatus({ connected: false, status: 'not_connected' });
    } catch (error) {
      console.error('Failed to disconnect calendar:', error);
      alert('Failed to disconnect calendar. Please try again.');
    }
  };

  const handleExport = (type: string) => {
    if (onExport) {
      onExport(type);
      return;
    }
    // Mock export functionality
    const dummyContent = type.includes('json') ? '{"data": []}' : 'id,title,date\n1,Task,2023-01-01';
    const blob = new Blob([dummyContent], { type: type.includes('json') ? 'application/json' : 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `export_${type}`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleRetakeOnboarding = () => {
    if (onRetakeOnboarding) {
      onRetakeOnboarding(resetData);
      return;
    }
    if (resetData) {
      if (confirm("Are you sure you want to reset all data and restart onboarding?")) {
        alert("Resetting data and restarting onboarding...");
      }
    } else {
      alert("Restarting onboarding flow...");
    }
  };

  return (
    <div className={styles.page}>
      {/* Header */}
      <header className={styles.header}>
        <div className={styles.headerLeft}>
          <span className={styles.pageLabel}>Preferences</span>
          <h1 className={styles.pageTitle}>Settings</h1>
        </div>
      </header>

      {/* Content */}
      <main className={styles.content}>
        <div className={styles.settingsContainer}>
          {/* Settings Grid */}
          <div className={styles.settingsGrid}>

            {/* Left Column */}
            <div className={styles.settingsColumn}>
              {/* Notifications Card */}
              <div className={styles.card}>
                <div className={styles.cardHeader}>
                  <div className={styles.cardIcon}>
                    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"></path>
                      <path d="M13.73 21a2 2 0 0 1-3.46 0"></path>
                    </svg>
                  </div>
                  <h2 className={styles.cardTitle}>Notifications</h2>
                </div>
                <p className={styles.cardDesc}>Get reminders for your tasks and daily check-ins.</p>
                <div className={styles.toggleRow}>
                  <span className={styles.toggleLabel}>Enable notifications</span>
                  <button
                    onClick={() => setNotificationsEnabled(!notificationsEnabled)}
                    className={`${styles.toggle} ${notificationsEnabled ? styles.toggleOn : ''}`}
                    type="button"
                  >
                    <span className={styles.toggleKnob} />
                  </button>
                </div>
              </div>

              {/* Onboarding Card */}
              <div className={styles.card}>
                <div className={styles.cardHeader}>
                  <div className={styles.cardIcon}>
                    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"></path>
                      <polyline points="3.27 6.96 12 12.01 20.73 6.96"></polyline>
                      <line x1="12" y1="22.08" x2="12" y2="12"></line>
                    </svg>
                  </div>
                  <h2 className={styles.cardTitle}>Onboarding</h2>
                </div>
                <p className={styles.cardDesc}>Revisit the setup flow or start fresh.</p>

                <button
                  onClick={handleRetakeOnboarding}
                  className={styles.actionBtn}
                  type="button"
                >
                  <span>Retake onboarding</span>
                  <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M5 12h14M12 5l7 7-7 7"/>
                  </svg>
                </button>

                <label className={styles.checkboxRow}>
                  <input
                    type="checkbox"
                    checked={resetData}
                    onChange={e => setResetData(e.target.checked)}
                    className={styles.checkbox}
                  />
                  <div className={styles.checkboxText}>
                    <span className={styles.checkboxLabel}>Reset everything</span>
                    <span className={styles.checkboxDesc}>Clears all your tasks, projects, and history.</span>
                  </div>
                </label>
              </div>
            </div>

            {/* Right Column */}
            <div className={styles.settingsColumn}>
              {/* Google Calendar Card */}
              <div className={styles.card}>
                <div className={styles.cardHeader}>
                  <div className={styles.cardIcon}>
                    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect>
                      <line x1="16" y1="2" x2="16" y2="6"></line>
                      <line x1="8" y1="2" x2="8" y2="6"></line>
                      <line x1="3" y1="10" x2="21" y2="10"></line>
                    </svg>
                  </div>
                  <h2 className={styles.cardTitle}>Google Calendar</h2>
                </div>
                <p className={styles.cardDesc}>
                  {calendarStatus?.connected
                    ? `Connected • ${calendarStatus.events_synced || 0} events synced`
                    : 'Connect your calendar so the AI can help schedule around your commitments.'}
                </p>

                {calendarStatus?.connected ? (
                  <>
                    <button
                      onClick={handleSyncCalendar}
                      className={styles.actionBtn}
                      type="button"
                      disabled={syncLoading}
                    >
                      <span>{syncLoading ? 'Syncing...' : 'Sync now'}</span>
                      <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <path d="M21.5 2v6h-6M2.5 22v-6h6M2 11.5a10 10 0 0 1 18.8-4.3M22 12.5a10 10 0 0 1-18.8 4.3"/>
                      </svg>
                    </button>
                    {calendarStatus.last_synced_at && (
                      <p className={styles.syncInfo}>
                        Last synced: {new Date(calendarStatus.last_synced_at).toLocaleString()}
                      </p>
                    )}
                    <button
                      onClick={handleDisconnectCalendar}
                      className={styles.disconnectBtn}
                      type="button"
                    >
                      Disconnect
                    </button>
                  </>
                ) : (
                  <button
                    onClick={handleConnectCalendar}
                    className={styles.connectBtn}
                    type="button"
                    disabled={calendarLoading}
                  >
                    <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect>
                      <line x1="16" y1="2" x2="16" y2="6"></line>
                      <line x1="8" y1="2" x2="8" y2="6"></line>
                      <line x1="3" y1="10" x2="21" y2="10"></line>
                    </svg>
                    <span>{calendarLoading ? 'Connecting...' : 'Connect Google Calendar'}</span>
                  </button>
                )}
              </div>

              {/* Export Data Card */}
              <div className={styles.card}>
                <div className={styles.cardHeader}>
                  <div className={styles.cardIcon}>
                    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                      <polyline points="7 10 12 15 17 10"></polyline>
                      <line x1="12" y1="15" x2="12" y2="3"></line>
                    </svg>
                  </div>
                  <h2 className={styles.cardTitle}>Export Data</h2>
                </div>
                <p className={styles.cardDesc}>Download your data in various formats.</p>

                <div className={styles.exportList}>
                  <ExportOption
                    label="Completed Dos"
                    format="CSV"
                    onClick={() => handleExport('completed_dos.csv')}
                  />
                  <ExportOption
                    label="Time log"
                    format="CSV"
                    onClick={() => handleExport('time_log.csv')}
                  />
                  <ExportOption
                    label="Notes"
                    format="JSON"
                    onClick={() => handleExport('notes.json')}
                  />
                </div>
              </div>

              {/* Help & Feedback Card */}
              <div className={styles.card}>
                <div className={styles.cardHeader}>
                  <div className={styles.cardIcon}>
                    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <circle cx="12" cy="12" r="10"></circle>
                      <path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"></path>
                      <line x1="12" y1="17" x2="12.01" y2="17"></line>
                    </svg>
                  </div>
                  <h2 className={styles.cardTitle}>Help & Feedback</h2>
                </div>
                <p className={styles.cardDesc}>Get support or share your ideas.</p>

                <div className={styles.linkList}>
                  <a href="#" className={styles.linkItem}>
                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M7 8h10M7 12h4m1 8l-4-4H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-3l-4 4z" />
                    </svg>
                    <span>Report a bug</span>
                  </a>
                  <a href="#" className={styles.linkItem}>
                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                    </svg>
                    <span>Request a feature</span>
                  </a>
                </div>

                <div className={styles.versionInfo}>
                  App Version 1.0.2 (Build 492)
                </div>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}

function ExportOption({ label, format, onClick }: { label: string; format: string; onClick: () => void }) {
  return (
    <button onClick={onClick} className={styles.exportItem} type="button">
      <div className={styles.exportIcon}>
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
          <polyline points="14 2 14 8 20 8"></polyline>
        </svg>
      </div>
      <div className={styles.exportText}>
        <span className={styles.exportLabel}>{label}</span>
        <span className={styles.exportFormat}>{format}</span>
      </div>
      <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={styles.exportArrow}>
        <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
        <polyline points="7 10 12 15 17 10"></polyline>
        <line x1="12" y1="15" x2="12" y2="3"></line>
      </svg>
    </button>
  );
}
