export function stageLabel(stage: string): string {
  const labels: Record<string, string> = {
    upload_validation: '上传校验',
    source_lookup: '来源检索',
    pack_analysis: '整合包分析',
    server_generation: '服务端生成',
    startup_verification: '启动验证',
    completed: '完成',
    queued: '排队中'
  };
  return labels[stage] ?? stage;
}

export function statusLabel(status: string): string {
  const labels: Record<string, string> = {
    queued: '排队中',
    running: '运行中',
    waiting_user_choice: '等待选择',
    succeeded: '已完成',
    failed: '失败',
    expired: '已过期'
  };
  return labels[status] ?? status;
}
