import { render, screen } from '@testing-library/react';
import { RecentTasks } from '../src/components/tasks/RecentTasks';

test('近期任务列表显示空状态', () => {
  render(<RecentTasks tasks={[]} />);

  expect(screen.getByText('暂无近期任务')).toBeInTheDocument();
});
