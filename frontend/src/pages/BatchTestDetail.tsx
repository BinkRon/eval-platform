import { useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { Button, Card, Col, Collapse, Descriptions, Row, Space, Spin, Statistic, Tag, Typography } from 'antd'
import { ArrowLeftOutlined, CheckCircleOutlined, CloseCircleOutlined } from '@ant-design/icons'
import type { TestResult } from '../api/batchTests'
import { useBatchTestDetail } from '../hooks/useBatchTests'

const TERM_REASON_MAP: Record<string, string> = {
  agent_hangup: 'Agent 挂断',
  sparring_end: '对练结束',
  max_rounds: '达到上限',
}

export default function BatchTestDetail() {
  const { id: projectId, bid: batchId } = useParams<{ id: string; bid: string }>()
  const navigate = useNavigate()

  if (!projectId || !batchId) return <Typography.Text type="danger">路由参数缺失</Typography.Text>

  const { data: batch, isLoading } = useBatchTestDetail(projectId, batchId)
  const [sortBy, setSortBy] = useState<'default' | 'failed_first'>('default')

  if (isLoading) return <Spin style={{ display: 'block', margin: '100px auto' }} />
  if (!batch) return <Typography.Text type="danger">批测不存在</Typography.Text>

  const results = [...(batch.test_results || [])]
  if (sortBy === 'failed_first') {
    results.sort((a, b) => (a.passed === b.passed ? 0 : a.passed ? 1 : -1))
  }

  // Stats
  const completedResults = results.filter((r) => r.status === 'completed')
  const passRate = completedResults.length > 0
    ? Math.round((batch.passed_cases / completedResults.length) * 100)
    : 0

  // Eval dimension averages
  const dimScores: Record<string, number[]> = {}
  for (const r of completedResults) {
    for (const s of r.eval_scores || []) {
      if (!dimScores[s.dimension]) dimScores[s.dimension] = []
      dimScores[s.dimension].push(s.score)
    }
  }

  // Checklist pass rates
  const checklistStats: Record<string, { total: number; passed: number }> = {}
  for (const r of completedResults) {
    for (const c of r.checklist_results || []) {
      if (!checklistStats[c.content]) checklistStats[c.content] = { total: 0, passed: 0 }
      checklistStats[c.content].total++
      if (c.passed) checklistStats[c.content].passed++
    }
  }

  return (
    <>
      <Space style={{ marginBottom: 16 }}>
        <Button icon={<ArrowLeftOutlined />} onClick={() => navigate(`/projects/${projectId}?tab=batch-tests`)}>
          返回
        </Button>
        <Typography.Title level={4} style={{ margin: 0 }}>批测详情</Typography.Title>
        <Tag color={batch.status === 'completed' ? 'success' : batch.status === 'running' ? 'processing' : 'default'}>
          {batch.status}
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
          <Card><Statistic title="通过/总数" value={`${batch.passed_cases}/${completedResults.length}`} /></Card>
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
        </Space>
      </div>

      {/* Test Results */}
      <Collapse
        items={results.map((r) => ({
          key: r.id,
          label: (
            <Space>
              {r.passed ? <CheckCircleOutlined style={{ color: '#52c41a' }} /> : <CloseCircleOutlined style={{ color: '#ff4d4f' }} />}
              <span>用例 {r.test_case_id?.slice(0, 8)}</span>
              <Tag color={r.passed ? 'green' : 'red'}>{r.passed ? '通过' : '未通过'}</Tag>
              <span>{r.actual_rounds} 轮</span>
              <Tag>{TERM_REASON_MAP[r.termination_reason || ''] || r.termination_reason}</Tag>
              {r.status === 'failed' && <Tag color="error">执行失败</Tag>}
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
    return <Typography.Text type="danger">错误：{result.error_message}</Typography.Text>
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
          <div style={{ maxHeight: 400, overflow: 'auto' }}>
            {result.conversation.map((msg, i) => (
              <div key={i} style={{ marginBottom: 12, textAlign: msg.role === 'user' ? 'left' : 'right' }}>
                <Tag color={msg.role === 'user' ? 'blue' : 'green'}>
                  {msg.role === 'user' ? '对练' : 'Agent'}
                </Tag>
                <div style={{
                  display: 'inline-block',
                  maxWidth: '70%',
                  padding: '8px 12px',
                  borderRadius: 8,
                  background: msg.role === 'user' ? '#e6f4ff' : '#f6ffed',
                  textAlign: 'left',
                }}>
                  {msg.content}
                </div>
              </div>
            ))}
          </div>
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
