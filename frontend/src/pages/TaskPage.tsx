import { useEffect, useState } from 'react';
import { TaskEventList } from '../components/tasks/TaskEventList';
import { TaskProgress } from '../components/tasks/TaskProgress';
import { TaskResultReport } from '../components/tasks/TaskResultReport';
import { artifactDownloadUrl, getTask, TaskDetail } from '../lib/api';

type TaskPageProps = {
  taskId?: string;
};

export function TaskPage({ taskId }: TaskPageProps) {
  const [task, setTask] = useState<TaskDetail | null>(null);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!taskId) return;
    const currentTaskId = taskId;
    let cancelled = false;
    let timer: number | undefined;

    async function loadTask() {
      try {
        const detail = await getTask(currentTaskId);
        if (cancelled) return;
        setTask(detail);
        setError('');
        if (detail.status === 'queued' || detail.status === 'running') {
          timer = window.setTimeout(loadTask, 1000);
        }
      } catch (loadError) {
        if (cancelled) return;
        setError(loadError instanceof Error ? loadError.message : '任务详情加载失败');
      }
    }

    loadTask();
    return () => {
      cancelled = true;
      if (timer) window.clearTimeout(timer);
    };
  }, [taskId]);

  if (!taskId) {
    return <TaskProgress message="正在加载任务详情" stage="queued" status="queued" />;
  }

  if (error) {
    return <p className="rounded-md border border-red-200 bg-red-50 p-4 text-sm text-red-900">{error}</p>;
  }

  if (!task) {
    return <TaskProgress message="正在加载任务详情" stage="queued" status="queued" />;
  }

  return (
    <section className="space-y-4">
      <TaskProgress message={task.progress_message} stage={task.stage} status={task.status} />
      <section className="rounded-lg border border-slate-200 bg-white p-4">
        <h2 className="text-base font-semibold text-slate-950">产物下载</h2>
        {task.artifacts.length === 0 ? (
          <p className="mt-2 text-sm text-slate-600">暂无可下载产物</p>
        ) : (
          <ul className="mt-3 space-y-2">
            {task.artifacts.map((artifact) => (
              <li key={artifact.id}>
                <a
                  className="inline-flex min-h-10 items-center rounded-md bg-emerald-700 px-3 text-sm font-medium text-white"
                  download
                  href={artifactDownloadUrl(task.id, artifact.id)}
                >
                  下载 {artifact.download_name}
                </a>
              </li>
            ))}
          </ul>
        )}
      </section>
      <TaskResultReport report={task.report} />
      <TaskEventList events={task.events} />
    </section>
  );
}
