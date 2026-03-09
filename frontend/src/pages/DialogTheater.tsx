import { useMemo, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { Card, Collapse, Select, Skeleton, Space, Spin, Tag, Typography } from 'antd'
import { useBatchTestDetail } from '../hooks/useBatchTests'
import { useProject } from '../hooks/useProjects'
import BreadcrumbNav from '../components/shared/BreadcrumbNav'
import ConversationBubbles from '../components/shared/ConversationBubbles'
import type { TestResult } from '../types/batchTest'

const TERM_REASON_MAP: Record<string, string> = {
  agent_hangup: 'Agent 挂断',
  sparring_end: '对练结束',
  max_rounds: '达到上限',
}

/** Status badge for the case switcher tabs */
function caseIcon(r: TestResult): string {
  if (r.status === 'failed') return '⚠️'
  if (r.status === 'running') return '⏳'
  if (r.status === 'pending') return '⏸'
  if (r.passed === true) return '✅'
  if (r.passed === false) return '❌'
  return '⏸'
}

type StatusFilter = 'all' | 'failed' | 'passed'

function CaseSwitcher({ results, activeId, onSwitch }: { results: TestResult[]; activeId: string; onSwitch: (id: string) => void }) {
  const [filter, setFilter] = useState<StatusFilter>('all')

  const filtered = useMemo(() => {
    if (filter === 'all') return results
    if (filter === 'failed') return results.filter((r) => r.status === 'failed' || (r.status === 'completed' && !r.passed))
    return results.filter((r) => r.status === 'completed' && r.passed)
  }, [results, filter])

  const completedCount = results.filter((r) => r.status === 'completed' || r.status === 'failed').length

  return (
    <div style={{ marginBottom: 16 }}>
      <Space style={{ marginBottom: 8 }}>
        <Select
          size="small"
          value={filter}
          onChange={setFilter}
          style={{ width: 120 }}
          options={[
            { value: 'all', label: '全部用例' },
            { value: 'failed', label: '未通过' },
            { value: 'passed', label: '已通过' },
          ]}
        />
        <Typography.Text type="secondary" style={{ fontSize: 12 }}>
          已完成 {completedCount}/{results.length}
        </Typography.Text>
      </Space>
      <div style={{ overflowX: 'auto', whiteSpace: 'nowrap', paddingBottom: 4 }}>
        <Space size={4} style={{ display: 'inline-flex' }}>
          {filtered.map((r) => {
            const isActive = r.id === activeId
            const label = r.test_case_name || `用例 ${r.test_case_id?.slice(0, 8) ?? '?'}`
            return (
              <Tag
                key={r.id}
                color={isActive ? 'blue' : undefined}
                style={{
                  cursor: 'pointer',
                  fontWeight: isActive ? 'bold' : 'normal',
                  borderWidth: isActive ? 2 : 1,
                }}
                onClick={() => onSwitch(r.id)}
              >
                {caseIcon(r)} {label}
              </Tag>
            )
          })}
        </Space>
      </div>
    </div>
  )
}

export default function DialogTheater() {
  const { id: projectId, bid: batchId, rid } = useParams<{ id: string; bid: string; rid: string }>()
  const navigate = useNavigate()
  const { data: batch, isLoading } = useBatchTestDetail(projectId ?? '', batchId ?? '')
  const { data: project } = useProject(projectId ?? '')

  // Sort: failed/not-passed first, then by original order
  const sortedResults = useMemo(() => {
    if (!batch) return []
    return [...batch.test_results].sort((a, b) => {
      const order = (r: TestResult) => {
        if (r.status === 'failed') return 0
        if (r.status === 'completed' && !r.passed) return 1
        if (r.status === 'running') return 2
        if (r.status === 'completed' && r.passed) return 3
        return 4
      }
      return order(a) - order(b)
    })
  }, [batch])

  const currentResult = useMemo(
    () => batch?.test_results.find((r) => r.id === rid) ?? null,
    [batch, rid],
  )

  if (!projectId || !batchId || !rid) return <Typography.Text type="danger">路由参数缺失</Typography.Text>
  if (isLoading) return <Spin style={{ display: 'block', margin: '100px auto' }} />
  if (!batch) return <Typography.Text type="danger">批测不存在</Typography.Text>
  if (!currentResult) return <Typography.Text type="danger">用例结果不存在</Typography.Text>

  const isRunning = currentResult.status === 'running'
  const isFailed = currentResult.status === 'failed'
  const hasConversation = (currentResult.conversation?.length ?? 0) > 0
  const hasJudgeResult = currentResult.checklist_results != null || currentResult.eval_scores != null

  // Determine judge status text
  let judgeStatusText: string | null = null
  if (isRunning && !currentResult.termination_reason) {
    judgeStatusText = '⏳ 对话进行中，待评判…'
  } else if (isRunning && currentResult.termination_reason) {
    judgeStatusText = '🔄 裁判评判中…'
  } else if (isFailed && !hasJudgeResult) {
    judgeStatusText = '⚠️ 执行失败，无评判结果'
  }

  return (
    <div>
      {/* Header */}
      <BreadcrumbNav items={[
        { title: '项目列表', path: '/projects' },
        { title: project?.name ?? '项目', path: `/projects/${projectId}` },
        { title: `批测${batch.agent_version_name ? ` · ${batch.agent_version_name}` : ''}`, path: `/projects/${projectId}/batch-tests/${batchId}` },
        { title: '对话剧场' },
      ]} />

      {/* 5.3: Case Switcher Tabs */}
      <CaseSwitcher
        results={sortedResults}
        activeId={rid!}
        onSwitch={(id) => navigate(`/projects/${projectId}/batch-tests/${batchId}/theater/${id}`, { replace: true })}
      />

      {/* 5.2: Dual-column layout (60/40) */}
      <div style={{ display: 'flex', gap: 16, alignItems: 'flex-start' }}>
        {/* 5.4: Left — Conversation Area (60%) */}
        <div style={{ flex: '0 0 60%', minWidth: 0 }}>
          <Card
            title={
              <span>
                对话记录
                {currentResult.actual_rounds != null && (
                  <Typography.Text type="secondary" style={{ marginLeft: 8, fontWeight: 'normal', fontSize: 13 }}>
                    {currentResult.actual_rounds} 轮
                  </Typography.Text>
                )}
                {isRunning && <Tag color="processing" style={{ marginLeft: 8 }}>实时</Tag>}
              </span>
            }
            size="small"
          >
            {hasConversation ? (
              <ConversationBubbles messages={currentResult.conversation!} height="calc(100vh - 320px)" />
            ) : (
              <Typography.Text type="secondary">
                {isRunning ? '⏳ 等待对话开始…' : '暂无对话数据'}
              </Typography.Text>
            )}

            {/* Termination reason */}
            {currentResult.termination_reason && (
              <div style={{ marginTop: 12, textAlign: 'center' }}>
                <Tag>{TERM_REASON_MAP[currentResult.termination_reason] || currentResult.termination_reason}</Tag>
              </div>
            )}

            {/* Error message */}
            {currentResult.error_message && (
              <div style={{ marginTop: 12 }}>
                <Typography.Text type="danger">{currentResult.error_message}</Typography.Text>
              </div>
            )}
          </Card>

          {/* Backstage info (collapsible) */}
          <Collapse
            size="small"
            style={{ marginTop: 12 }}
            items={[
              ...(currentResult.sparring_prompt_snapshot
                ? [{
                    key: 'persona',
                    label: '对练角色卡 & System Prompt',
                    children: (
                      <Typography.Paragraph>
                        <pre style={{ whiteSpace: 'pre-wrap', fontSize: 12, margin: 0 }}>
                          {currentResult.sparring_prompt_snapshot}
                        </pre>
                      </Typography.Paragraph>
                    ),
                  }]
                : []),
            ]}
          />
        </div>

        {/* 5.5: Right — Judge Area (40%) */}
        <div style={{ flex: '0 0 40%', minWidth: 0 }}>
          {/* 5.6: Running status text */}
          {judgeStatusText && (
            <Card size="small" style={{ marginBottom: 12, textAlign: 'center' }}>
              <Typography.Text type="secondary" style={{ fontSize: 14 }}>
                {judgeStatusText}
              </Typography.Text>
            </Card>
          )}

          {/* Checklist Results */}
          {currentResult.checklist_results && currentResult.checklist_results.length > 0 && (
            <Card title="Checklist 结果" size="small" style={{ marginBottom: 12 }}>
              {currentResult.checklist_results.map((c, i) => {
                const isMust = c.level === 'must'
                const failed = !c.passed
                return (
                  <div key={i} style={{ marginBottom: 8 }}>
                    <div>
                      <Tag color={isMust ? 'red' : 'orange'}>{isMust ? '🔴 必过' : '🟡 重要'}</Tag>
                      <span style={{ fontWeight: failed && isMust ? 'bold' : 'normal', color: failed && isMust ? '#ff4d4f' : undefined }}>
                        {c.passed ? '✅' : '❌'} {c.content}
                      </span>
                    </div>
                    {c.reason && (
                      <Typography.Text type="secondary" style={{ fontSize: 12, marginLeft: 24 }}>
                        {c.reason}
                      </Typography.Text>
                    )}
                  </div>
                )
              })}
            </Card>
          )}

          {/* Evaluation Scores */}
          {currentResult.eval_scores && currentResult.eval_scores.length > 0 && (
            <Card title="Evaluation 评分" size="small" style={{ marginBottom: 12 }}>
              {currentResult.eval_scores.map((s, i) => (
                <div key={i} style={{ marginBottom: 8 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span>{s.dimension}</span>
                    <span>
                      {'⭐'.repeat(Math.max(0, Math.min(3, Math.round(s.score))))} ({s.score}/3)
                    </span>
                  </div>
                  {s.reason && (
                    <Typography.Text type="secondary" style={{ fontSize: 12 }}>
                      {s.reason}
                    </Typography.Text>
                  )}
                </div>
              ))}
            </Card>
          )}

          {/* Judge Summary */}
          {currentResult.judge_summary && (
            <Card title="裁判总结" size="small" style={{ marginBottom: 12 }}>
              <Typography.Paragraph style={{ margin: 0 }}>
                {currentResult.judge_summary}
              </Typography.Paragraph>
            </Card>
          )}

          {/* Empty state placeholder when no judge data yet */}
          {!judgeStatusText && !hasJudgeResult && !currentResult.judge_summary && currentResult.status !== 'completed' && (
            <Card size="small" style={{ marginBottom: 12 }}>
              <Skeleton active title={{ width: '60%' }} paragraph={{ rows: 3, width: ['100%', '80%', '50%'] }} />
              <div style={{ textAlign: 'center', marginTop: 16 }}>
                <Typography.Text type="secondary">
                  {currentResult.status === 'pending' ? '⏸ 用例待执行' : '评判结果将在此处展示'}
                </Typography.Text>
              </div>
            </Card>
          )}

          {/* Judge Prompt (collapsible) */}
          {currentResult.judge_prompt_snapshot && (
            <Collapse
              size="small"
              items={[{
                key: 'judge-prompt',
                label: '裁判 Prompt',
                children: (
                  <Typography.Paragraph>
                    <pre style={{ whiteSpace: 'pre-wrap', fontSize: 12, margin: 0 }}>
                      {currentResult.judge_prompt_snapshot}
                    </pre>
                  </Typography.Paragraph>
                ),
              }]}
            />
          )}
        </div>
      </div>
    </div>
  )
}
