'use client';

import { useRouter } from 'next/navigation';
import SettingsPage from '../../components/SettingsPage';

export default function SettingsRoute() {
  const router = useRouter();

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
