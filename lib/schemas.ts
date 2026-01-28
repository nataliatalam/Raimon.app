'use client';

import { z } from 'zod';

// ============ User & Auth ============

export const UserProfileSchema = z.object({
  id: z.string(),
  email: z.string().email(),
  name: z.string().nullable().optional(),
  onboarding_completed: z.boolean().optional(),
  onboarding_step: z.number().nullable().optional(),
});

export const AuthSuccessPayloadSchema = z.object({
  user: UserProfileSchema,
  token: z.string(),
  refresh_token: z.string(),
});

// ============ API Response Wrappers ============

export const ApiSuccessResponseSchema = <T extends z.ZodTypeAny>(dataSchema: T) =>
  z.object({
    success: z.literal(true),
    data: dataSchema,
    message: z.string().optional(),
  });

export const ApiErrorResponseSchema = z.object({
  success: z.literal(false),
  message: z.string().optional(),
  error: z
    .object({
      code: z.string().optional(),
      message: z.string().optional(),
    })
    .optional(),
});

// ============ Dashboard ============

export const DashboardTaskSchema = z.object({
  id: z.string(),
  title: z.string(),
  description: z.string().nullable().optional(),
  project_id: z.string().nullable().optional(),
  project_name: z.string().nullable().optional(),
  status: z.string().optional(),
  priority: z.string().optional(),
  estimated_duration: z.number().nullable().optional(),
  deadline: z.string().nullable().optional(),
});

export const DashboardTasksPayloadSchema = z.object({
  pending: z.array(DashboardTaskSchema),
  completed: z.array(DashboardTaskSchema),
  summary: z.object({
    total_pending: z.number(),
    total_completed: z.number(),
  }),
});

export const DashboardSummaryPayloadSchema = z.object({
  greeting: z.string(),
  current_state: z.object({
    status: z.string(),
    current_task: z
      .object({
        id: z.string(),
        title: z.string(),
        elapsed_time: z.number(),
        estimated_remaining: z.number(),
      })
      .nullable(),
  }),
  today: z.object({
    tasks_completed: z.number(),
    tasks_remaining: z.number(),
    focus_time: z.number(),
    energy_level: z.number().nullable().optional(),
  }),
  projects: z.array(
    z.object({
      id: z.string(),
      name: z.string(),
      progress: z.number(),
      status: z.string(),
    })
  ),
  insights: z.array(
    z.object({
      type: z.string(),
      message: z.string(),
    })
  ),
  streaks: z.record(z.string(), z.number()),
});

// ============ Projects ============

export const ProjectApiRecordSchema = z.object({
  id: z.string(),
  name: z.string(),
  description: z.string().nullable().optional(),
  status: z.enum(['active', 'archived', 'completed']),
  priority: z.number().nullable().optional(),
  color: z.string().nullable().optional(),
  icon: z.string().nullable().optional(),
  progress: z.number().nullable().optional(),
  archived_at: z.string().nullable().optional(),
  created_at: z.string().nullable().optional(),
});

// ============ Flower Points & Graveyard ============

export const FlowerTransactionSchema = z.object({
  id: z.string(),
  amount: z.number(),
  type: z.enum(['earned', 'spent']),
  reason: z.string(),
  project_id: z.string().optional(),
  created_at: z.string(),
});

export const FlowerPointsPayloadSchema = z.object({
  balance: z.number(),
  transactions: z.array(FlowerTransactionSchema).optional(),
});

export const FlowerSchema = z.object({
  id: z.string(),
  name: z.string(),
  emoji: z.string(),
  cost: z.number(),
  days_added: z.number(),
  placed_at: z.string().optional(),
});

export const GraveyardMetaPayloadSchema = z.object({
  project_id: z.string(),
  flowers: z.array(FlowerSchema),
  epitaph: z.string().optional(),
  expiry_date: z.string(),
});

// ============ File Uploads ============

export const ProjectFileSchema = z.object({
  id: z.string(),
  project_id: z.string(),
  file_name: z.string(),
  file_path: z.string(),
  file_size: z.number().optional(),
  mime_type: z.string().optional(),
  uploaded_at: z.string().optional(),
});
