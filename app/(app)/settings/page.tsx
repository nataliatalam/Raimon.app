'use client';

import { useRouter, useSearchParams } from 'next/navigation';
import { useEffect } from 'react';
import SettingsPage from '../../components/SettingsPage';

export default function SettingsRoute() {
  const router = useRouter();
  const searchParams = useSearchParams();

  useEffect(() => {
    const calendarParam = searchParams.get('calendar');
    if (calendarParam === 'connected') {
      alert('Google Calendar connected successfully!');
      router.replace('/settings');
    } else if (calendarParam === 'error') {
      alert('Failed to connect Google Calendar. Please try again.');
      router.replace('/settings');
    }
  }, [searchParams, router]);

  function handleRetakeOnboarding(resetData: boolean) {
    if (resetData) {
      if (confirm("Are you sure you want to reset all data and restart onboarding?")) {
        // TODO: Call API to reset user data
        router.push('/onboarding');
      }
    } else {
      router.push('/onboarding');
    }
  }

  function handleExport(type: string) {
    // TODO: Implement real export from API
    const dummyContent = type.includes('json') ? '{"data": []}' : 'id,title,date\n1,Task,2023-01-01';
    const blob = new Blob([dummyContent], { type: type.includes('json') ? 'application/json' : 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `export_${type}`;
    a.click();
    URL.revokeObjectURL(url);
  }

  return (
    <SettingsPage
      onRetakeOnboarding={handleRetakeOnboarding}
      onExport={handleExport}
    />
  );
}
