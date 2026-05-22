export type TaskCreated = {
  task_id: string;
  status: 'queued';
  message: string;
};

export type TaskSummary = {
  id: string;
  type: 'upload_generate' | 'official_search';
  status: string;
  progress_message: string;
  created_at: string;
};

const API_BASE = import.meta.env.VITE_API_BASE ?? '';

async function parseJson<T>(response: Response): Promise<T> {
  const body = await response.json();
  if (!response.ok) {
    throw new Error(body.detail ?? '请求失败');
  }
  return body as T;
}

export async function createOfficialSearchTask(query: string): Promise<TaskCreated> {
  const response = await fetch(`${API_BASE}/api/search/official-server`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query })
  });
  return parseJson<TaskCreated>(response);
}

export async function uploadPack(file: File): Promise<TaskCreated> {
  const form = new FormData();
  form.append('file', file);
  const response = await fetch(`${API_BASE}/api/uploads`, {
    method: 'POST',
    body: form
  });
  return parseJson<TaskCreated>(response);
}

export async function listTasks(): Promise<TaskSummary[]> {
  const response = await fetch(`${API_BASE}/api/tasks`);
  return parseJson<TaskSummary[]>(response);
}
