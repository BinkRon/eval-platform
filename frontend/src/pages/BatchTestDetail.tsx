import { useMemo, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { Button, Card, Col, Row, Space, Spin, Statistic, Table, Tag, Typography } from 'antd'
import type { ColumnsType } from 'antd/es/table'
import type { TestResult } from '../types/batchTest'
import { useBatchTestDetail } from '../hooks/useBatchTests'
import { useProject } from '../hooks/useProjects'
import BreadcrumbNav from '../components/shared/BreadcrumbNav'
import { SEMANTIC_COLORS } from '../theme/themeConfig'

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

type SortMode = 'failed_first' | 'by_index' | 'by_rounds'

export default function BatchTestDetail() {
  const { id: projectId, bid: batchId } = useParams<{ id: string; bid: string }>()
  const navigate = useNavigate()
  const { data: batch, isLoading } = useBatchTestDetail(projectId ?? '', batchId ?? '')
  const { data: project } = useProject(projectId ?? '')
  const [sortBy, setSortBy] = useState<SortMode>('failed_first')

  const { dimScores, checklistStats } = useMemo(() => {
    if (!batch) return { dimScores: {} as Record<string, number[]>, checklistStats: {} as Record<string, { total: number; passed: number; level: string }> }
    const completed = (batch.test_results || []).filter((r) => r.status === 'completed')
    const scores: Record<string, number[]> = {}
    for (const r of completed) {
      for (const s of r.eval_scores || []) {
        if (!scores[s.dimension]) scores[s.dimension] = []
        scores[s.dimension].push(s.score)
      }
    }
    const stats: Record<string, { total: number; passed: number; level: string }> = {}
    for (const r of completed) {
      for (const c of r.checklist_results || []) {
        if (!stats[c.content]) stats[c.content] = { total: 0, passed: 0, level: c.level }
        stats[c.content].total++
        if (c.passed) stats[c.content].passed++
      }
    }
    return { dimScores: scores, checklistStats: stats }
  }, [batch])

  const sortedResults = useMemo(() => {
    if (!batch) return []
    const results = [...(batch.test_results || [])]
    if (sortBy === 'failed_first') {
      results.sort((a, b) => {
        const order = (r: TestResult) => {
          if (r.status === 'failed') return 0
          if (r.status === 'completed' && !r.passed) return 1
          if (r.status === 'completed' && r.passed) return 2
          if (r.status === 'running') return 3
          return 4 // pending
        }
        return order(a) - order(b)
      })
    } else if (sortBy === 'by_rounds') {
      results.sort((a, b) => (b.actual_rounds ?? 0) - (a.actual_rounds ?? 0))
    }
    // by_index: keep original order
    return results
  }, [batch, sortBy])

  if (!projectId || !batchId) return <Typography.Text type="danger">路由参数缺失</Typography.Text>
  if (isLoading) return <Spin style={{ display: 'block', margin: '100px auto' }} />
  if (!batch) return <Typography.Text type="danger">批测不存在</Typography.Text>

  const denominator = batch.status === 'completed' ? batch.total_cases : batch.completed_cases
  const passRate = denominator > 0 ? Math.round((batch.passed_cases / denominator) * 100) : 0

  const columns: ColumnsType<TestResult> = [
    {
      title: '用例名称',
      dataIndex: 'test_case_name',
      key: 'name',
      render: (name: string | null, r: TestResult) =>
        name ? `「${name}」` : r.test_case_id ? `用例 ${r.test_case_id.slice(0, 8)}` : '-',
    },
    {
      title: '结果',
      key: 'result',
      width: 120,
      filters: [
        { text: '✅ 通过', value: 'passed' },
        { text: '❌ 未通过', value: 'not_passed' },
        { text: '⚠️ 执行失败', value: 'failed' },
        { text: '⏳ 进行中', value: 'running' },
        { text: '⏸ 等待中', value: 'pending' },
      ],
      onFilter: (value, r) => {
        if (value === 'passed') return r.status === 'completed' && r.passed === true
        if (value === 'not_passed') return r.status === 'completed' && r.passed === false
        return r.status === value
      },
      render: (_: unknown, r: TestResult) => {
        if (r.status === 'running') return <Tag color="processing">⏳ 进行中</Tag>
        if (r.status === 'pending') return <Tag>⏸ 等待中</Tag>
        if (r.status === 'failed') return <Tag color="error">⚠️ 执行失败</Tag>
        return r.passed
          ? <Tag color="success">✅ 通过</Tag>
          : <Tag color="error">❌ 未通过</Tag>
      },
    },
    {
      title: '轮次',
      dataIndex: 'actual_rounds',
      key: 'rounds',
      width: 80,
      render: (rounds: number | null) => rounds ?? '-',
    },
    {
      title: '终止原因',
      dataIndex: 'termination_reason',
      key: 'termination',
      width: 120,
      render: (reason: string | null) =>
        reason ? (TERM_REASON_MAP[reason] || reason) : '-',
    },
    {
      title: '操作',
      key: 'action',
      width: 100,
      render: (_: unknown, r: TestResult) => {
        const canEnter = r.status !== 'pending'
        return (
          <Button
            type="link"
            size="small"
            disabled={!canEnter}
            onClick={() => navigate(`/projects/${projectId}/batch-tests/${batchId}/theater/${r.id}`)}
          >
            进入剧场
          </Button>
        )
      },
    },
  ]

  return (
    <>
      {/* Header */}
      <BreadcrumbNav items={[
        { title: '项目列表', path: '/projects' },
        { title: project?.name ?? '项目', path: `/projects/${projectId}` },
        { title: `批测${batch.agent_version_name ? ` · ${batch.agent_version_name}` : ''}` },
      ]} />
      <Space style={{ marginBottom: 16 }}>
        <Typography.Title level={4} style={{ margin: 0 }}>
          批测详情{batch.agent_version_name ? ` · ${batch.agent_version_name}` : ''}
        </Typography.Title>
        <Tag color={BATCH_STATUS_MAP[batch.status]?.color ?? 'default'}>
          {BATCH_STATUS_MAP[batch.status]?.label ?? batch.status}
        </Tag>
        <Typography.Text type="secondary">
          通过率：{batch.passed_cases}/{batch.total_cases} ({passRate}%)
        </Typography.Text>
      </Space>

      {/* Summary Stats */}
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={6}>
          <Card size="small"><Statistic title="总用例数" value={batch.total_cases} /></Card>
        </Col>
        <Col span={6}>
          <Card size="small">
            <Statistic
              title="通过率"
              value={passRate}
              suffix="%"
              valueStyle={{ color: passRate >= 80 ? SEMANTIC_COLORS.passRateUp : SEMANTIC_COLORS.passRateDown }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card size="small"><Statistic title="通过/总数" value={`${batch.passed_cases}/${batch.total_cases}`} /></Card>
        </Col>
        <Col span={6}>
          <Card size="small">
            <Statistic
              title="完成时间"
              value={batch.completed_at ? new Date(batch.completed_at).toLocaleString() : '-'}
            />
          </Card>
        </Col>
      </Row>

      {/* Checklist + Eval Summary */}
      <Row gutter={16} style={{ marginBottom: 24 }}>
        {Object.keys(checklistStats).length > 0 && (
          <Col span={12}>
            <Card title="Checklist 通过率" size="small">
              {Object.entries(checklistStats).map(([content, stat]) => {
                const pct = Math.round((stat.passed / stat.total) * 100)
                const isMust = stat.level === 'must'
                const isFullPass = stat.passed === stat.total
                return (
                  <div key={content} style={{ marginBottom: 4 }}>
                    <Tag color={isMust ? 'red' : 'orange'}>{isMust ? '必过' : '重要'}</Tag>
                    <Tag color={isFullPass ? 'green' : 'red'}>
                      {stat.passed}/{stat.total} {pct}%
                    </Tag>
                    <span style={{ color: isMust && !isFullPass ? SEMANTIC_COLORS.passRateDown : undefined, fontWeight: isMust && !isFullPass ? 'bold' : undefined }}>
                      {content}
                    </span>
                  </div>
                )
              })}
            </Card>
          </Col>
        )}
        {Object.keys(dimScores).length > 0 && (
          <Col span={12}>
            <Card title="Evaluation 维度均分" size="small">
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
          </Col>
        )}
      </Row>

      {/* Sort Toggle + Table */}
      <div style={{ marginBottom: 8 }}>
        <Space>
          <span>排序：</span>
          <Button size="small" type={sortBy === 'failed_first' ? 'primary' : 'default'} onClick={() => setSortBy('failed_first')}>未通过优先</Button>
          <Button size="small" type={sortBy === 'by_index' ? 'primary' : 'default'} onClick={() => setSortBy('by_index')}>按用例序号</Button>
          <Button size="small" type={sortBy === 'by_rounds' ? 'primary' : 'default'} onClick={() => setSortBy('by_rounds')}>按轮次</Button>
        </Space>
      </div>

      <Table
        dataSource={sortedResults}
        columns={columns}
        rowKey="id"
        pagination={false}
        size="middle"
      />
    </>
  )
}
