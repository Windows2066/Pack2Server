import { render, screen } from '@testing-library/react';
import { TaskProgress } from '../src/components/tasks/TaskProgress';

test('任务进度组件展示当前阶段和中文说明', () => {
  render(<TaskProgress stage="source_lookup" message="正在检索官方服务端" status="running" />);

  expect(screen.getByText('来源检索')).toBeInTheDocument();
  expect(screen.getByText('正在检索官方服务端')).toBeInTheDocument();
});
