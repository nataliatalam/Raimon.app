export enum CalendarView {
  DAY = 'day',
  WEEK = 'week',
  MONTH = 'month',
}

export interface CalendarEvent {
  id: string;
  title: string;
  startTime: Date;
  endTime: Date;
  project?: string;
  projectId?: string;
  category: 'WORK' | 'PERSONAL' | 'OTHER';
  description?: string;
  source?: 'manual' | 'project-deadline' | 'task-deadline';
  relatedId?: string;
}

export interface CalendarProject {
  id: string;
  name: string;
  category: 'WORK' | 'PERSONAL' | 'OTHER';
}
