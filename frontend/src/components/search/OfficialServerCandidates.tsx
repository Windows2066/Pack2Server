type Candidate = {
  source: string;
  pack_name: string;
  pack_version?: string | null;
  match_reason: string;
};

export function OfficialServerCandidates({ candidates }: { candidates: Candidate[] }) {
  if (candidates.length === 0) {
    return <p className="rounded-md border border-amber-200 bg-amber-50 p-3 text-sm text-amber-900">未找到官方服务端。已检索来源：CurseForge、Modrinth、FTB。</p>;
  }

  return (
    <ul className="space-y-3">
      {candidates.map((candidate) => (
        <li className="rounded-md border border-slate-200 bg-white p-4" key={`${candidate.source}-${candidate.pack_name}`}>
          <div className="font-medium text-slate-900">{candidate.pack_name}</div>
          <div className="mt-1 text-sm text-slate-600">来源：{candidate.source}；版本：{candidate.pack_version ?? '未指定'}</div>
          <div className="mt-2 text-sm text-slate-700">{candidate.match_reason}</div>
        </li>
      ))}
    </ul>
  );
}
