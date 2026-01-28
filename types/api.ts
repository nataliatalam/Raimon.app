export type UserProfile = {
  id: string;
  email: string;
  name?: string | null;
  onboarding_completed?: boolean;
  onboarding_step?: number | null;
};

export type SessionData = {
  accessToken: string | null;
  refreshToken: string | null;
  user: UserProfile | null;
};

export type AuthSuccessPayload = {
  user: UserProfile;
  token: string;
  refresh_token: string;
};

export type ApiSuccessResponse<TData> = {
  success: true;
  data: TData;
  message?: string;
};

export type ApiErrorResponse = {
  success: false;
  message?: string;
  error?: {
    code?: string;
    message?: string;
  };
};

export type DashboardTask = {
  id: string;
  title: string;
  description?: string | null;
  project_id?: string | null;
  project_name?: string | null;
  status?: string;
  priority?: string;
  estimated_duration?: number | null;
  deadline?: string | null;
};

export type DashboardTasksPayload = {
  pending: DashboardTask[];
  completed: DashboardTask[];
  summary: {
    total_pending: number;
    total_completed: number;
  };
};

export type DashboardSummaryPayload = {
  greeting: string;
  current_state: {
    status: string;
    current_task: {
      id: string;
      title: string;
      elapsed_time: number;
      estimated_remaining: number;
    } | null;
  };
  today: {
    tasks_completed: number;
    tasks_remaining: number;
    focus_time: number;
    energy_level?: number | null;
  };
  projects: Array<{
    id: string;
    name: string;
    progress: number;
    status: string;
  }>;
  insights: Array<{ type: string; message: string }>;
  streaks: Record<string, number>;
};

export type ProjectApiRecord = {
  id: string;
  name: string;
  description?: string | null;
  status: 'active' | 'archived' | 'completed';
  priority?: number | null;
  color?: string | null;
  icon?: string | null;
  progress?: number | null;
  archived_at?: string | null;
  created_at?: string | null;
};

export type FlowerTransaction = {
  id: string;
  amount: number;
  type: 'earned' | 'spent';
  reason: string;
  project_id?: string;
  created_at: string;
};

export type FlowerPointsPayload = {
  balance: number;
  transactions?: FlowerTransaction[];
};

export type GraveyardMetaPayload = {
  project_id: string;
  flowers: Array<{
    id: string;
    name: string;
    emoji: string;
    cost: number;
    days_added: number;
    placed_at?: string;
  }>;
  epitaph?: string;
  expiry_date: string;
};

export type ProjectFile = {
  id: string;
  project_id: string;
  file_name: string;
  file_path: string;
  file_size?: number;
  mime_type?: string;
  uploaded_at?: string;
};

