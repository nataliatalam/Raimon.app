// app/(app)/dashboard/focus/page.tsx
'use client';

import { useEffect, useMemo, useState } from 'react';
import { useRouter } from 'next/navigation';
import FocusChamber from '../../../components/FocusChamber';
import ImStuck from '../../../components/ImStuck';

export default function FocusPage() {
  const router = useRouter();
  const [stored, setStored] = useState<any>(null);
  const [stuckOpen, setStuckOpen] = useState(false);

  useEffect(() => {
    try {
      const raw = sessionStorage.getItem('raimon_active_task');
      if (raw) setStored(JSON.parse(raw));
    } catch {
      setStored(null);
    }
  }, []);

  const task = useMemo(() => {
    const title = stored?.title ?? stored?.name ?? 'Focus Session';

    const rawMinutes =
      stored?.minutes ??
      stored?.durationMinutes ??
      stored?.duration ??
      stored?.estimateMinutes ??
      25;

    // ✅ fuerza a número seguro
    const minutesNum =
      typeof rawMinutes === 'number'
        ? rawMinutes
        : Number(String(rawMinutes).replace(/[^\d.]/g, '')) || 25;

    return {
      ...stored,
      title,
      minutes: minutesNum,
      durationMinutes: minutesNum,
      duration: `${minutesNum} min`, // ✅ tu FocusTask espera string opcional
    } as any;
  }, [stored]);

  const demoResources = useMemo(
    () => [
      {
        id: '1',
        kind: 'doc' as const,
        name: 'Q1 Strategy.docx',
        action: 'View document',
        onClick: () => alert('Open doc (demo)'),
      },
      {
        id: '2',
        kind: 'sheet' as const,
        name: 'Budget.xlsx',
        action: 'Open sheet',
        onClick: () => alert('Open sheet (demo)'),
      },
      {
        id: '3',
        kind: 'link' as const,
        name: 'Figma link',
        action: 'Open link',
        onClick: () => {
          if (typeof window !== 'undefined') {
            window.open('https://www.figma.com', '_blank', 'noopener,noreferrer');
          }
        },
      },
    ],
    []
  );

  return (
    <>
      <FocusChamber
        task={task}
        resources={demoResources}
        onStuck={() => setStuckOpen(true)}
        onDone={() => router.push('/dashboard')}
      />
      <ImStuck open={stuckOpen} onClose={() => setStuckOpen(false)} />
    </>
  );
}
