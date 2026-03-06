import { useMemo, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { Alert, Button, Card, Col, Collapse, Descriptions, Divider, Row, Space, Spin, Statistic, Tag, Typography } from 'antd'
import { ArrowLeftOutlined, CheckCircleOutlined, CloseCircleOutlined } from '@ant-design/icons'
import type { TestResult } from '../api/batchTests'
import { useBatchTestDetail } from '../hooks/useBatchTests'

const BATCH_STATUS_MAP: Record<string, { color: string; label: string }> = {
  completed: { color: 'success', label: '已完成' },
  running: { color: 'processing', label: '运行中' },
  failed: { color: 'error', label: '失败' },
  pending: { color: 'default', label: '待执行' },
}

const TERM_REASON_MAP: Record<string, string> = {
  agent_hangup: 'Agent 挂断',
  sparring_end: '对练结束',
  max_rounds: '达到上限',
}

export default function BatchTestDetail() {
  const { id: projectId, bid: batchId } = useParams<{ id: string; bid: string }>()
  const navigate = useNavigate()
  const { data: batch, isLoading } = useBatchTestDetail(projectId ?? '', batchId ?? '')
  const [sortBy, setSortBy] = useState<'default' | 'failed_first' | 'by_rounds'>('default')

  // Hooks must be called before any conditional returns
  const { dimScores, checklistStats } = useMemo(() => {
    if (!batch) return { dimScores: {}, checklistStats: {} }
    const completed = (batch.test_results || []).filter((r) => r.status === 'completed')
    const scores: Record<string, number[]> = {}
    for (const r of completed) {
      for (const s of r.eval_scores || []) {
        if (!scores[s.dimension]) scores[s.dimension] = []
        scores[s.dimension].push(s.score)
      }
    }
    const stats: Record<string, { total: number; passed: number }> = {}
    for (const r of completed) {
      for (const c of r.checklist_results || []) {
        if (!stats[c.content]) stats[c.content] = { total: 0, passed: 0 }
        stats[c.content].total++
        if (c.passed) stats[c.content].passed++
      }
    }
    return { dimScores: scores, checklistStats: stats }
  }, [batch])

  if (!projectId || !batchId) return <Typography.Text type="danger">路由参数缺失</Typography.Text>
  if (isLoading) return <Spin style={{ display: 'block', margin: '100px auto' }} />
  if (!batch) return <Typography.Text type="danger">批测不存在</Typography.Text>

  const results = [...(batch.test_results || [])]
  if (sortBy === 'failed_first') {
    results.sort((a, b) => (a.passed === b.passed ? 0 : a.passed ? 1 : -1))
  }
  if (sortBy === 'by_rounds') {
    results.sort((a, b) => (b.actual_rounds ?? 0) - (a.actual_rounds ?? 0))
  }

  // Stats
  const denominator = batch.status === 'completed' ? batch.total_cases : (batch.completed_cases || batch.total_cases)
  const passRate = denominator > 0
    ? Math.round((batch.passed_cases / denominator) * 100)
    : 0

  return (
    <>
      <Space style={{ marginBottom: 16 }}>
        <Button icon={<ArrowLeftOutlined />} onClick={() => navigate(`/projects/${projectId}?tab=batch-tests`)}>
          返回
        </Button>
        <Typography.Title level={4} style={{ margin: 0 }}>批测详情</Typography.Title>
        <Tag color={BATCH_STATUS_MAP[batch.status]?.color ?? 'default'}>
          {BATCH_STATUS_MAP[batch.status]?.label ?? batch.status}
        </Tag>
      </Space>

      {/* Summary Stats */}
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={6}>
          <Card><Statistic title="总用例数" value={batch.total_cases} /></Card>
        </Col>
        <Col span={6}>
          <Card><Statistic title="通过率" value={passRate} suffix="%" valueStyle={{ color: passRate >= 80 ? '#3f8600' : '#cf1322' }} /></Card>
        </Col>
        <Col span={6}>
          <Card><Statistic title="通过/总数" value={`${batch.passed_cases}/${batch.total_cases}`} /></Card>
        </Col>
        <Col span={6}>
          <Card><Statistic title="完成时间" value={batch.completed_at ? new Date(batch.completed_at).toLocaleString() : '-'} /></Card>
        </Col>
      </Row>

      {/* Checklist Summary */}
      {Object.keys(checklistStats).length > 0 && (
        <Card title="Checklist 通过率" size="small" style={{ marginBottom: 16 }}>
          {Object.entries(checklistStats).map(([content, stat]) => (
            <div key={content} style={{ marginBottom: 4 }}>
              <Tag color={stat.passed === stat.total ? 'green' : 'red'}>
                {stat.passed}/{stat.total}
              </Tag>
              {content}
            </div>
          ))}
        </Card>
      )}

      {/* Eval Dimension Averages */}
      {Object.keys(dimScores).length > 0 && (
        <Card title="Evaluation 维度均分" size="small" style={{ marginBottom: 16 }}>
          <Row gutter={16}>
            {Object.entries(dimScores).map(([dim, scores]) => {
              const avg = (scores.reduce((a, b) => a + b, 0) / scores.length).toFixed(1)
              return (
                <Col key={dim} span={8}>
                  <Statistic title={dim} value={avg} suffix="/ 3" />
                </Col>
              )
            })}
          </Row>
        </Card>
      )}

      {/* Sort Toggle */}
      <div style={{ marginBottom: 8 }}>
        <Space>
          <span>排序：</span>
          <Button size="small" type={sortBy === 'default' ? 'primary' : 'default'} onClick={() => setSortBy('default')}>默认</Button>
          <Button size="small" type={sortBy === 'failed_first' ? 'primary' : 'default'} onClick={() => setSortBy('failed_first')}>未通过优先</Button>
          <Button size="small" type={sortBy === 'by_rounds' ? 'primary' : 'default'} onClick={() => setSortBy('by_rounds')}>按轮次</Button>
        </Space>
      </div>

      {/* Test Results */}
      <Collapse
        items={results.map((r) => ({
          key: r.id,
          label: (
            <Space>
              {r.status === 'failed'
                ? <CloseCircleOutlined style={{ color: '#ff4d4f' }} />
                : r.passed
                  ? <CheckCircleOutlined style={{ color: '#52c41a' }} />
                  : <CloseCircleOutlined style={{ color: '#ff4d4f' }} />
              }
              <span>{r.test_case_name ? `「${r.test_case_name}」` : `用例 ${r.test_case_id?.slice(0, 8)}`}</span>
              {r.status === 'failed'
                ? <Tag color="error">执行失败</Tag>
                : <Tag color={r.passed ? 'green' : 'red'}>{r.passed ? '通过' : '未通过'}</Tag>
              }
              {r.actual_rounds != null && <span>{r.actual_rounds} 轮</span>}
              {r.termination_reason && (
                <Tag>{TERM_REASON_MAP[r.termination_reason] || r.termination_reason}</Tag>
              )}
            </Space>
          ),
          children: <TestResultExpand result={r} />,
        }))}
      />
    </>
  )
}

function TestResultExpand({ result }: { result: TestResult }) {
  if (result.status === 'failed') {
    return (
      <>
        <Alert type="error" message={result.error_message || '执行失败'} style={{ marginBottom: 16 }} />
        {result.conversation && result.conversation.length > 0 && (
          <>
            <Divider>对话记录（评判前）</Divider>
            <Card size="small">
              <ConversationBubbles messages={result.conversation} />
            </Card>
          </>
        )}
      </>
    )
  }

  return (
    <>
      {/* Checklist */}
      {result.checklist_results && result.checklist_results.length > 0 && (
        <Descriptions title="Checklist 结果" column={1} size="small" style={{ marginBottom: 16 }}>
          {result.checklist_results.map((c, i) => (
            <Descriptions.Item
              key={i}
              label={
                <Space>
                  <Tag color={c.level === 'must' ? 'red' : 'orange'}>{c.level === 'must' ? '必过' : '重要'}</Tag>
                  {c.content}
                </Space>
              }
            >
              <Tag color={c.passed ? 'green' : 'red'}>{c.passed ? '通过' : '未通过'}</Tag>
              {c.reason && <Typography.Text type="secondary"> {c.reason}</Typography.Text>}
            </Descriptions.Item>
          ))}
        </Descriptions>
      )}

      {/* Eval Scores */}
      {result.eval_scores && result.eval_scores.length > 0 && (
        <Descriptions title="Evaluation 评分" column={3} size="small" style={{ marginBottom: 16 }}>
          {result.eval_scores.map((s, i) => (
            <Descriptions.Item key={i} label={s.dimension}>
              {'⭐'.repeat(s.score)} ({s.score}/3)
              {s.reason && <div><Typography.Text type="secondary">{s.reason}</Typography.Text></div>}
            </Descriptions.Item>
          ))}
        </Descriptions>
      )}

      {/* Conversation */}
      {result.conversation && (
        <Card title="对话记录" size="small" style={{ marginBottom: 16 }}>
          <ConversationBubbles messages={result.conversation} />
        </Card>
      )}

      {/* Judge Summary */}
      {result.judge_summary && (
        <Card title="裁判总结" size="small">
          <Typography.Paragraph>{result.judge_summary}</Typography.Paragraph>
        </Card>
      )}
    </>
  )
}

function ConversationBubbles({ messages }: { messages: Array<{ role: string; content: string }> }) {
  return (
    <div style={{ maxHeight: 400, overflow: 'auto' }}>
      {messages.map((msg, i) => (
        <div key={i} style={{ marginBottom: 12, textAlign: msg.role === 'user' ? 'left' : 'right' }}>
          <Tag color={msg.role === 'user' ? 'blue' : 'green'}>
            {msg.role === 'user' ? '对练' : 'Agent'}
          </Tag>
          <div style={{
            display: 'inline-block', maxWidth: '70%',
            padding: '8px 12px', borderRadius: 8,
            background: msg.role === 'user' ? '#e6f4ff' : '#f6ffed',
            textAlign: 'left',
          }}>
            {msg.content}
          </div>
        </div>
      ))}
    </div>
  )
}
