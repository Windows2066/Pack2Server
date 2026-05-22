import { render, screen } from '@testing-library/react';
import { TaskPage } from '../src/pages/TaskPage';

afterEach(() => {
  vi.unstubAllGlobals();
});

test('任务页展示产物下载链接和启动验证报告', async () => {
  vi.stubGlobal(
    'fetch',
    vi.fn().mockResolvedValue(
      new Response(
        JSON.stringify({
          id: 'task-1',
          type: 'upload_generate',
          status: 'succeeded',
          stage: 'completed',
          progress_message: '服务端生成完成，可以下载产物',
          created_at: '2026-05-22T00:00:00Z',
          input_summary: 'pack.mrpack',
          events: [
            {
              stage: 'startup_verification',
              level: 'info',
              message: '启动验证已跳过',
              created_at: '2026-05-22T00:00:01Z'
            }
          ],
          artifacts: [
            {
              id: 'server-archive',
              kind: 'server_archive',
              download_name: 'task-1-server.zip',
              expires_at: '2026-05-23T00:00:00Z'
            }
          ],
          report: '# 服务端生成完成\n\n启动验证已跳过'
        }),
        { status: 200, headers: { 'Content-Type': 'application/json' } }
      )
    )
  );

  render(<TaskPage taskId="task-1" />);

  const link = await screen.findByRole('link', { name: '下载 task-1-server.zip' });
  expect(link).toHaveAttribute('href', '/api/tasks/task-1/artifacts/server-archive/download');
  expect(screen.getAllByText(/启动验证已跳过/).length).toBeGreaterThan(0);
});
