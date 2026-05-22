import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { GenerateServerForm } from '../src/components/upload/GenerateServerForm';

test('上传表单显示中文提示并提交文件', async () => {
  const user = userEvent.setup();
  const onSubmit = vi.fn();
  render(<GenerateServerForm onSubmit={onSubmit} isSubmitting={false} />);

  const input = screen.getByLabelText('选择整合包压缩包');
  const file = new File(['demo'], 'pack.mrpack', { type: 'application/octet-stream' });
  await user.upload(input, file);
  await user.click(screen.getByRole('button', { name: '开始制作服务端' }));

  expect(onSubmit).toHaveBeenCalledWith(file);
});
