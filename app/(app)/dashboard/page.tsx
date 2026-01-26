'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';

import DailyCheckIn from '../../components/DailyCheckIn';
import TasksPage, { Task } from '../../components/TasksPage';

export default function Page() {
  const router = useRouter();
  const [stage, setStage] = useState<'checkin' | 'tasks'>('checkin');

  useEffect(() => {
    try {
      const checkedIn = sessionStorage.getItem('raimon_checked_in');
      if (checkedIn === 'true') {
        setStage('tasks');
      }
    } catch {}
  }, []);

  if (stage === 'checkin') {

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
  
        try {
          sessionStorage.setItem('raimon_active_task', JSON.stringify(task));
        } catch {}

        router.push('/dashboard/focus');
      }}
      onFinish={() => {
        
      }}
    />
  );
}
