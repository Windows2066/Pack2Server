import { FormEvent, useState } from 'react';
import { Button } from '../ui/Button';

type OfficialServerSearchFormProps = {
  onSubmit: (query: string) => void;
  isSubmitting: boolean;
};

export function OfficialServerSearchForm({ onSubmit, isSubmitting }: OfficialServerSearchFormProps) {
  const [query, setQuery] = useState('');
  const [error, setError] = useState('');

  function handleSubmit(event: FormEvent) {
    event.preventDefault();
    const trimmed = query.trim();
    if (!trimmed) {
      setError('请输入整合包名称或描述');
      return;
    }
    setError('');
    onSubmit(trimmed);
  }

  return (
    <form className="space-y-3" onSubmit={handleSubmit}>
      <label className="block">
        <span className="text-sm font-medium text-slate-900">描述你想要的服务端</span>
        <textarea
          className="mt-2 min-h-24 w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm focus:border-emerald-600 focus:outline-none focus:ring-2 focus:ring-emerald-100"
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          placeholder="例如：我想要 ATM10 最新版服务端"
        />
      </label>
      {error ? <p className="text-sm text-red-700">{error}</p> : null}
      <Button disabled={isSubmitting} type="submit">
        {isSubmitting ? '正在检索' : '查找官方服务端'}
      </Button>
    </form>
  );
}
