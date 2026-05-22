import { FormEvent, useState } from 'react';
import { Button } from '../ui/Button';
import { UploadDropzone } from './UploadDropzone';

type GenerateServerFormProps = {
  onSubmit: (file: File) => void;
  isSubmitting: boolean;
};

export function GenerateServerForm({ onSubmit, isSubmitting }: GenerateServerFormProps) {
  const [file, setFile] = useState<File | null>(null);
  const [error, setError] = useState('');

  function handleSubmit(event: FormEvent) {
    event.preventDefault();
    if (!file) {
      setError('请先选择整合包压缩包');
      return;
    }
    setError('');
    onSubmit(file);
  }

  return (
    <form className="space-y-4" onSubmit={handleSubmit}>
      <UploadDropzone file={file} onFileChange={setFile} />
      {error ? <p className="text-sm text-red-700">{error}</p> : null}
      <Button disabled={isSubmitting} type="submit">
        {isSubmitting ? '正在提交' : '开始制作服务端'}
      </Button>
    </form>
  );
}
