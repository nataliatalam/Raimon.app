// app/(app)/dashboard/page.tsx
'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';

import DailyCheckIn from '../../components/DailyCheckIn';
import TasksPage, { Task } from '../../components/TasksPage';

export default function Page() {
  const router = useRouter();
  const [stage, setStage] = useState<'checkin' | 'tasks'>('checkin');

  // Check if user has already completed checkin this session
  useEffect(() => {
    try {
      const checkedIn = sessionStorage.getItem('raimon_checked_in');
      if (checkedIn === 'true') {
        setStage('tasks');
      }
    } catch {}
  }, []);

  if (stage === 'checkin') {
    // ✅ Your DailyCheckIn currently does NOT accept props, so render it plain.
    // We'll control navigation here so you can reach Tasks + Focus.
    return (
      <DailyCheckIn
        onComplete={() => {
          try {
            sessionStorage.setItem('raimon_checked_in', 'true');
          } catch {}
          setStage('tasks');
        }}
      />
    );
  }

  return (
    <TasksPage
      onDo={(task: Task) => {
        // Save selected task so Focus page can read it
        try {
          sessionStorage.setItem('raimon_active_task', JSON.stringify(task));
        } catch {}

        router.push('/dashboard/focus');
      }}
      onFinish={() => {
        // optional: store something
      }}
    />
  );
}
