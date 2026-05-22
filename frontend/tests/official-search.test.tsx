import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { OfficialServerCandidates } from '../src/components/search/OfficialServerCandidates';
import { OfficialServerSearchForm } from '../src/components/search/OfficialServerSearchForm';

test('自然语言检索表单提交中文查询', async () => {
  const user = userEvent.setup();
  const onSubmit = vi.fn();
  render(<OfficialServerSearchForm onSubmit={onSubmit} isSubmitting={false} />);

  await user.type(screen.getByLabelText('描述你想要的服务端'), 'ATM10 最新版');
  await user.click(screen.getByRole('button', { name: '查找官方服务端' }));

  expect(onSubmit).toHaveBeenCalledWith('ATM10 最新版');
});

test('未找到官方服务端时列出已检索来源', () => {
  render(<OfficialServerCandidates candidates={[]} />);

  expect(screen.getByText(/未找到官方服务端/)).toHaveTextContent('CurseForge');
  expect(screen.getByText(/未找到官方服务端/)).toHaveTextContent('Modrinth');
  expect(screen.getByText(/未找到官方服务端/)).toHaveTextContent('FTB');
});
