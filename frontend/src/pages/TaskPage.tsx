import { TaskProgress } from '../components/tasks/TaskProgress';

export function TaskPage() {
  return <TaskProgress message="正在加载任务详情" stage="queued" status="queued" />;
}
