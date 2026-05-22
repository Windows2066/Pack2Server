type TaskEvent = {
  stage: string;
  level: string;
  message: string;
  created_at: string;
};

export function TaskEventList({ events }: { events: TaskEvent[] }) {
  if (events.length === 0) return <p className="text-sm text-slate-600">暂无任务事件</p>;
  return (
    <ol className="space-y-2">
      {events.map((event, index) => (
        <li className="rounded-md border border-slate-200 bg-white p-3 text-sm" key={`${event.created_at}-${index}`}>
          <span className="font-medium text-slate-900">{event.message}</span>
          <span className="ml-2 text-slate-500">{event.stage}</span>
        </li>
      ))}
    </ol>
  );
}
