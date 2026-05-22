import type { TaskSummary } from '../../lib/api';
import { statusLabel } from '../../lib/task-status';

export function RecentTasks({ tasks }: { tasks: TaskSummary[] }) {
  if (tasks.length === 0) {
    return <p className="rounded-md border border-slate-200 bg-white p-4 text-sm text-slate-600">暂无近期任务</p>;
  }

  return (
    <ul className="space-y-2">
      {tasks.map((task) => (
        <li className="rounded-md border border-slate-200 bg-white p-3" key={task.id}>
          <div className="text-sm font-medium text-slate-900">{task.progress_message}</div>
          <div className="mt-1 text-xs text-slate-500">{statusLabel(task.status)}</div>
        </li>
      ))}
    </ul>
  );
}
