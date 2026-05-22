import { useEffect, useState } from 'react';
import { createOfficialSearchTask, listTasks, TaskSummary, uploadPack } from '../lib/api';
import { GenerateServerForm } from '../components/upload/GenerateServerForm';
import { OfficialServerSearchForm } from '../components/search/OfficialServerSearchForm';
import { RecentTasks } from '../components/tasks/RecentTasks';

export function HomePage() {
  const [mode, setMode] = useState<'upload' | 'search'>('upload');
  const [message, setMessage] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [tasks, setTasks] = useState<TaskSummary[]>([]);

  useEffect(() => {
    listTasks().then(setTasks).catch(() => setTasks([]));
  }, []);

  async function handleUpload(file: File) {
    setIsSubmitting(true);
    try {
      const result = await uploadPack(file);
      setMessage(result.message);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : '提交失败');
    } finally {
      setIsSubmitting(false);
    }
  }

  async function handleSearch(query: string) {
    setIsSubmitting(true);
    try {
      const result = await createOfficialSearchTask(query);
      setMessage(result.message);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : '检索失败');
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <main className="mx-auto grid min-h-dvh max-w-6xl gap-6 px-4 py-8 md:grid-cols-[1.2fr_0.8fr]">
      <section className="space-y-6">
        <div>
          <p className="text-sm font-medium text-emerald-700">Minecraft 服务端工具</p>
          <h1 className="mt-2 text-3xl font-semibold text-slate-950">服务端整合包生成器</h1>
          <p className="mt-3 max-w-2xl text-slate-700">上传客户端整合包生成服务端，或直接查找官方服务端。</p>
        </div>
        <div className="inline-flex rounded-lg border border-slate-200 bg-white p-1">
          <button aria-pressed={mode === 'upload'} className={`rounded-md px-3 py-2 text-sm ${mode === 'upload' ? 'bg-emerald-700 text-white' : 'text-slate-700'}`} onClick={() => setMode('upload')} type="button">
            上传生成
          </button>
          <button aria-pressed={mode === 'search'} className={`rounded-md px-3 py-2 text-sm ${mode === 'search' ? 'bg-emerald-700 text-white' : 'text-slate-700'}`} onClick={() => setMode('search')} type="button">
            查找官方服务端
          </button>
        </div>
        <div className="rounded-xl border border-slate-200 bg-slate-50 p-5">
          {mode === 'upload' ? <GenerateServerForm isSubmitting={isSubmitting} onSubmit={handleUpload} /> : <OfficialServerSearchForm isSubmitting={isSubmitting} onSubmit={handleSearch} />}
        </div>
        {message ? <p aria-live="polite" className="rounded-md bg-emerald-50 p-3 text-sm text-emerald-900">{message}</p> : null}
      </section>
      <aside className="space-y-3">
        <h2 className="text-lg font-semibold text-slate-950">近期任务</h2>
        <RecentTasks tasks={tasks} />
      </aside>
    </main>
  );
}
