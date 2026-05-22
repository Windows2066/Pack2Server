export function TaskResultReport({ report }: { report?: string | null }) {
  if (!report) return <p className="text-sm text-slate-600">暂无结果报告</p>;
  return <pre className="whitespace-pre-wrap rounded-lg bg-slate-950 p-4 text-sm text-slate-50">{report}</pre>;
}
