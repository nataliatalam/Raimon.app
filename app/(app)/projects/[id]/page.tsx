'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import ProjectDetailView from '../../../components/projects/projectdetail';
import { useSession } from '../../../components/providers/SessionProvider';
import { apiFetch, ApiError } from '../../../../lib/api-client';
import type { ApiSuccessResponse } from '../../../../types/api';

interface ProjectApiResponse {
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
  type?: string | null;
  timeline?: string | null;
  deadline?: string | null;
  motivations?: string[] | null;
  tasks?: Array<{
    id: string;
    title: string;
    completed: boolean;
    dueDate?: string;
    priority?: 'high' | 'medium' | 'low';
    subtasks?: Array<{ id: string; title: string; completed: boolean }>;
    dependsOn?: string;
    blocker?: string;
    recurring?: string;
  }> | null;
  notes?: string | null;
  links?: Array<{
    id: string;
    title: string;
    url: string;
    type: 'file' | 'link';
  }> | null;
}

interface ProjectForView {
  id: string;
  name: string;
  description: string;
  type: 'work' | 'personal';
  status: 'active' | 'paused' | 'completed';
  color: string;
  timeframe: string;
  deadline: string;
  tasks: Array<{
    id: string;
    title: string;
    completed: boolean;
    dueDate?: string;
    priority?: 'high' | 'medium' | 'low';
    subtasks: Array<{ id: string; title: string; completed: boolean }>;
    dependsOn?: string;
    blocker?: string;
    recurring?: string;
  }>;
  notes: string;
  motivations: string[];
  links: Array<{
    id: string;
    title: string;
    url: string;
    type: 'file' | 'link';
  }>;
  activity: Array<{
    id: string;
    action: string;
    detail: string;
    time: string;
  }>;
}

function mapApiToProject(data: ProjectApiResponse): ProjectForView {
  return {
    id: data.id,
    name: data.name,
    description: data.description ?? '',
    type: data.icon === 'personal' ? 'personal' : 'work',
    status: data.status === 'archived' ? 'paused' : data.status,
    color: data.color ?? '#F97316',
    timeframe: data.timeline ?? 'Ongoing',
    deadline: data.deadline ?? 'No deadline',
    tasks: (data.tasks ?? []).map((t) => ({
      ...t,
      subtasks: t.subtasks ?? [],
    })),
    notes: data.notes ?? '',
    motivations: data.motivations ?? [],
    links: data.links ?? [],
    activity: [],
  };
}

export default function ProjectDetailPage() {
  const params = useParams();
  const router = useRouter();
  const { session, status } = useSession();
  const [project, setProject] = useState<ProjectForView | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [saving, setSaving] = useState(false);

  const projectId = params.id as string;

  useEffect(() => {
    if (status !== 'ready' || !session.accessToken || !projectId) return;
    fetchProject();
  }, [status, session.accessToken, projectId]);

  async function fetchProject() {
    setLoading(true);
    setError('');
    try {
      const response = await apiFetch<ApiSuccessResponse<{ project: ProjectApiResponse }>>(
        `/api/projects/${projectId}`
      );
      setProject(mapApiToProject(response.data.project));
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError('Failed to load project');
      }
    } finally {
      setLoading(false);
    }
  }

  async function handleSave(updatedProject: ProjectForView) {
    setSaving(true);
    try {
      // Transform tasks to snake_case for backend
      const tasksForBackend = updatedProject.tasks.map((task) => ({
        id: task.id,
        title: task.title,
        completed: task.completed,
        due_date: task.dueDate,
        priority: task.priority,
        subtasks: task.subtasks,
        depends_on: task.dependsOn,
        blocker: task.blocker,
        recurring: task.recurring,
      }));

      await apiFetch(`/api/projects/${projectId}`, {
        method: 'PUT',
        body: {
          name: updatedProject.name,
          description: updatedProject.description,
          notes: updatedProject.notes,
          tasks: tasksForBackend,
        },
      });
      setProject(updatedProject);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError('Failed to save project');
      }
    } finally {
      setSaving(false);
    }
  }

  function handleBack() {
    router.push('/projects');
  }

  if (loading) {
    return (
      <div style={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: '#F9F8F4',
        fontFamily: "'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif",
      }}>
        Loading project...
      </div>
    );
  }

  if (error || !project) {
    return (
      <div style={{
        minHeight: '100vh',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        gap: '16px',
        background: '#F9F8F4',
        fontFamily: "'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif",
      }}>
        <p style={{ color: '#EF4444' }}>{error || 'Project not found'}</p>
        <button
          onClick={handleBack}
          style={{
            padding: '10px 20px',
            background: '#1A1A1A',
            border: 'none',
            borderRadius: '10px',
            color: '#fff',
            cursor: 'pointer',
            fontSize: '14px',
            fontWeight: 600,
          }}
        >
          Back to Projects
        </button>
      </div>
    );
  }

  return (
    <ProjectDetailView
      project={project}
      onBack={handleBack}
      onSave={handleSave}
    />
  );
}
