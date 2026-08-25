import { Project, ProjectFile, RoutingLog, DeployResult, RoutingEvent } from './types';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';

export async function generateProject(
  prompt: string,
  projectType?: string,
  preferredProvider?: string
): Promise<{
  project_id: string;
  project_type: string;
  requires_confirmation: boolean;
  ambiguity_details?: string;
  status: string;
}> {
  const res = await fetch(`${API_BASE}/generate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      prompt,
      project_type: projectType,
      preferred_provider: preferredProvider || 'anthropic',
    }),
  });

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({ detail: 'Generation failed' }));
    throw new Error(errorData.detail || 'Failed to initiate generation');
  }

  return res.json();
}

export function streamGeneration(
  projectId: string,
  onEvent: (event: RoutingEvent) => void,
  onError?: (err: any) => void
): () => void {
  const eventSource = new EventSource(`${API_BASE}/generate/${projectId}/stream`);

  eventSource.onmessage = (event) => {
    try {
      const data: RoutingEvent = JSON.parse(event.data);
      onEvent(data);
    } catch (e) {
      console.error('Error parsing SSE event:', e);
    }
  };

  eventSource.onerror = (err) => {
    console.error('SSE connection error:', err);
    if (onError) onError(err);
    eventSource.close();
  };

  return () => {
    eventSource.close();
  };
}

export async function getProject(projectId: string): Promise<Project> {
  const res = await fetch(`${API_BASE}/projects/${projectId}`);
  if (!res.ok) throw new Error('Failed to load project');
  return res.json();
}

export async function getProjectFiles(projectId: string): Promise<ProjectFile[]> {
  const res = await fetch(`${API_BASE}/projects/${projectId}/files`);
  if (!res.ok) throw new Error('Failed to load project files');
  const data = await res.json();
  return data.files || [];
}

export async function getRoutingLogs(projectId: string): Promise<RoutingLog[]> {
  const res = await fetch(`${API_BASE}/projects/${projectId}/routing-logs`);
  if (!res.ok) return [];
  const data = await res.json();
  return data.logs || [];
}

export async function deployProject(projectId: string): Promise<DeployResult> {
  const res = await fetch(`${API_BASE}/projects/${projectId}/deploy`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({}),
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({ detail: 'Deploy failed' }));
    throw new Error(errorData.detail || 'Deploy failed');
  }
  return res.json();
}

export async function submitFeedback(
  projectId: string,
  rating: 'good' | 'bad',
  comment?: string
): Promise<void> {
  await fetch(`${API_BASE}/feedback`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ project_id: projectId, rating, comment }),
  });
}

export async function addCollaborator(
  projectId: string,
  userEmail: string,
  role: 'editor' | 'viewer' = 'editor'
): Promise<void> {
  const res = await fetch(`${API_BASE}/projects/${projectId}/collaborators`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ user_email: userEmail, role }),
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({ detail: 'Failed to add collaborator' }));
    throw new Error(errorData.detail || 'Failed to add collaborator');
  }
}

export async function logManualOverride(
  projectId: string,
  fileId: string,
  taskType: string,
  preferredModel: string
): Promise<void> {
  await fetch(`${API_BASE}/projects/${projectId}/files/${fileId}/override`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ task_type: taskType, preferred_model: preferredModel }),
  });
}
