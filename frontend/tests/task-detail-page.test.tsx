import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
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

test('任务页展示自然语言候选并提交选择', async () => {
  const user = userEvent.setup();
  const fetchMock = vi
    .fn()
    .mockResolvedValueOnce(
      new Response(
        JSON.stringify({
          id: 'task-choice',
          type: 'official_search',
          status: 'waiting_user_choice',
          stage: 'candidate_selection',
          progress_message: '请选择要检索的候选整合包',
          created_at: '2026-05-22T00:00:00Z',
          events: [],
          artifacts: [],
          official_candidates: [
            {
              query: 'ATM10',
              version_hint: 'latest',
              source_hint: null,
              confidence: 0.86,
              reason: '用户提到 ATM10 最新版'
            }
          ],
          report: 'DeepSeek 返回多个可能候选，请选择一个后继续检索。'
        }),
        { status: 200, headers: { 'Content-Type': 'application/json' } }
      )
    )
    .mockResolvedValueOnce(
      new Response(JSON.stringify({ task_id: 'task-choice', status: 'queued', message: '已选择候选整合包' }), {
        status: 202,
        headers: { 'Content-Type': 'application/json' }
      })
    )
    .mockResolvedValueOnce(
      new Response(
        JSON.stringify({
          id: 'task-choice',
          type: 'official_search',
          status: 'queued',
          stage: 'source_lookup',
          progress_message: '已选择候选整合包，等待查询官方服务端',
          created_at: '2026-05-22T00:00:00Z',
          events: [],
          artifacts: [],
          official_candidates: [],
          report: null
        }),
        { status: 200, headers: { 'Content-Type': 'application/json' } }
      )
    );
  vi.stubGlobal('fetch', fetchMock);

  render(<TaskPage taskId="task-choice" />);
  await user.click(await screen.findByRole('button', { name: '选择 ATM10' }));

  expect(fetchMock).toHaveBeenCalledWith('/api/search/official-server/task-choice/candidates/0', {
    method: 'POST'
  });
  expect(await screen.findByText('已选择候选整合包，等待查询官方服务端')).toBeInTheDocument();
});
