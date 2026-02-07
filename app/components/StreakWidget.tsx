'use client';

import React, { useEffect, useState } from 'react';
import { Flame } from 'lucide-react';
import styles from './DailyCheckIn.module.css';

const DAYS_OF_WEEK = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];

type StreakWidgetProps = {
  streakCount: number;
};

const StreakWidget: React.FC<StreakWidgetProps> = ({ streakCount }) => {
  const [currentDayIndex, setCurrentDayIndex] = useState<number | null>(null);

  useEffect(() => {
    setCurrentDayIndex(new Date().getDay());
  }, []);

  return (
    <div className={styles.streakSubtle}>
      <div className={styles.streakHeader}>
        <div className={styles.streakIconBox}>
          <Flame className={styles.streakIcon} />
        </div>
        <div>
          <div className={styles.streakCount}>{streakCount}</div>
          <span className={styles.streakLabel}>Day Streak</span>
        </div>
      </div>
      <div className={styles.streakDays}>
        {DAYS_OF_WEEK.map((day, index) => {
          const isToday = currentDayIndex !== null && index === currentDayIndex;
          const isCompleted = currentDayIndex !== null && (index < currentDayIndex || isToday);
          return (
            <div key={day} className={styles.streakDayCol}>
              <div
                className={`${styles.streakDot} ${
                  isToday ? styles.today : isCompleted ? styles.completed : ''
                }`}
              />
              <span className={`${styles.streakDayName} ${isToday ? styles.active : ''}`}>{day}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default StreakWidget;
