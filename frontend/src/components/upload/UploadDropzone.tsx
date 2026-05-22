type UploadDropzoneProps = {
  file: File | null;
  onFileChange: (file: File | null) => void;
};

export function UploadDropzone({ file, onFileChange }: UploadDropzoneProps) {
  return (
    <label className="block rounded-lg border border-dashed border-slate-300 bg-white p-5">
      <span className="block text-sm font-medium text-slate-900">选择整合包压缩包</span>
      <span className="mt-1 block text-sm text-slate-600">支持 .zip 和 .mrpack，提交前会先做基础校验。</span>
      <input
        aria-label="选择整合包压缩包"
        className="mt-4 block w-full text-sm"
        type="file"
        accept=".zip,.mrpack"
        onChange={(event) => onFileChange(event.currentTarget.files?.[0] ?? null)}
      />
      {file ? <span className="mt-3 block text-sm text-emerald-700">已选择：{file.name}</span> : null}
    </label>
  );
}
