import { stageLabel, statusLabel } from '../../lib/task-status';

type TaskProgressProps = {
  stage: string;
  status: string;
  message: string;
};

export function TaskProgress({ stage, status, message }: TaskProgressProps) {
  return (
    <section aria-live="polite" className="rounded-lg border border-slate-200 bg-white p-4">
      <div className="text-sm font-medium text-slate-500">{statusLabel(status)}</div>
      <h2 className="mt-1 text-lg font-semibold text-slate-950">{stageLabel(stage)}</h2>
      <p className="mt-2 text-sm text-slate-700">{message}</p>
    </section>
  );
}
