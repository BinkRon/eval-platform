import { useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { Button, Card, Col, message, Popconfirm, Progress, Row, Space, Spin, Table, Tag, Tooltip, Typography } from 'antd'
import {
  PlayCircleOutlined,
  EyeOutlined,
  DeleteOutlined,
  CheckCircleFilled,
  ExclamationCircleFilled,
  ApiOutlined,
  ExperimentOutlined,
  AuditOutlined,
  RobotOutlined,
} from '@ant-design/icons'
import { useProject, useProjectReadiness } from '../hooks/useProjects'
import { useBatchTests, useDeleteBatchTest } from '../hooks/useBatchTests'
import CreateBatchModal from '../components/batch-test/CreateBatchModal'
import BreadcrumbNav from '../components/shared/BreadcrumbNav'
import type { BatchTest } from '../types/batchTest'
import { SEMANTIC_COLORS } from '../theme/themeConfig'

const STATUS_MAP: Record<string, { color: string; label: string }> = {
  pending: { color: 'default', label: '等待中' },
  running: { color: 'processing', label: '运行中' },
  completed: { color: 'success', label: '已完成' },
  failed: { color: 'error', label: '失败' },
}

function BatchProgress({ batch }: { batch: BatchTest }) {
  const percent = batch.total_cases > 0 ? Math.round((batch.completed_cases / batch.total_cases) * 100) : 0

  if (batch.status === 'completed' || batch.status === 'failed') {
    if (batch.status === 'failed' && batch.completed_cases === 0) {
      return <span>—</span>
    }
    return <span>{batch.passed_cases}/{batch.total_cases} 通过</span>
  }

  return <Progress percent={percent} size="small" format={() => `${batch.completed_cases}/${batch.total_cases}`} />
}

function PassRate({ batch }: { batch: BatchTest }) {
  if (batch.status === 'failed' && batch.completed_cases === 0) return <span>—</span>
  if (batch.completed_cases === 0) return <span>—</span>
  const rate = Math.round((batch.passed_cases / batch.completed_cases) * 100)
  return <span>{batch.passed_cases}/{batch.completed_cases} ({rate}%)</span>
}

interface ReadinessCardProps {
  title: string
  icon: React.ReactNode
  ready: boolean
  message: string
  onClick: () => void
}

function ReadinessCard({ title, icon, ready, message, onClick }: ReadinessCardProps) {
  return (
    <Card
      hoverable
      size="small"
      onClick={onClick}
      style={{ cursor: 'pointer' }}
    >
      <Space direction="vertical" size={4} style={{ width: '100%' }}>
        <Space>
          <span style={{ fontSize: 18 }}>{icon}</span>
          <Typography.Text strong>{title}</Typography.Text>
        </Space>
        <Space size={4}>
          {ready ? (
            <CheckCircleFilled style={{ color: SEMANTIC_COLORS.passRateUp }} />
          ) : (
            <ExclamationCircleFilled style={{ color: SEMANTIC_COLORS.colorWarning }} />
          )}
          <Typography.Text type="secondary" style={{ fontSize: 13 }}>{message}</Typography.Text>
        </Space>
        <Typography.Text type="secondary" style={{ fontSize: 12 }}>点击配置 →</Typography.Text>
      </Space>
    </Card>
  )
}

export default function ProjectWorkbench() {
  const { id } = useParams<{ id: string }>()
  const { data: project, isLoading } = useProject(id ?? '')
  const { data: readiness } = useProjectReadiness(id ?? '')
  const { data: batches, isLoading: batchLoading } = useBatchTests(id ?? '')
  const deleteMutation = useDeleteBatchTest(id ?? '')
  const navigate = useNavigate()
  const [modalOpen, setModalOpen] = useState(false)

  if (!id) return <Typography.Text type="danger">项目 ID 缺失</Typography.Text>
  if (isLoading) return <Spin style={{ display: 'block', margin: '100px auto' }} />
  if (!project) return <Typography.Text type="danger">项目不存在</Typography.Text>

  const allReady = readiness?.all_ready ?? false

  const unreadyItems = readiness
    ? [
        !readiness.agent_version.ready && 'Agent 版本',
        !readiness.test_case.ready && '测试用例',
        !readiness.judge_config.ready && '裁判配置',
        !readiness.model_config_status.ready && '模型配置',
      ].filter((x): x is string => !!x)
    : []

  const columns = [
    {
      title: '状态',
      key: 'status',
      width: 100,
      render: (_: unknown, r: BatchTest) => {
        const s = STATUS_MAP[r.status] || STATUS_MAP.pending
        return <Tag color={s.color}>{s.label}</Tag>
      },
    },
    {
      title: 'Agent 版本',
      dataIndex: 'agent_version_name',
      key: 'agent_version_name',
      render: (v: string | null) => v || '-',
    },
    {
      title: '用例数',
      dataIndex: 'total_cases',
      key: 'total_cases',
      width: 80,
    },
    {
      title: '进度',
      key: 'progress',
      width: 200,
      render: (_: unknown, r: BatchTest) => <BatchProgress batch={r} />,
    },
    {
      title: '通过率',
      key: 'pass_rate',
      width: 140,
      render: (_: unknown, r: BatchTest) => <PassRate batch={r} />,
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (v: string) => new Date(v).toLocaleString(),
    },
    {
      title: '操作',
      key: 'actions',
      width: 140,
      render: (_: unknown, r: BatchTest) => (
        <Space size={0}>
          <Button
            type="link"
            icon={<EyeOutlined />}
            onClick={() => navigate(`/projects/${id}/batch-tests/${r.id}`)}
            disabled={r.status === 'pending'}
          >
            查看
          </Button>
          <Popconfirm
            title="确认删除该批测记录？"
            description="删除后不可恢复"
            onConfirm={async () => {
              try {
                await deleteMutation.mutateAsync(r.id)
                message.success('已删除')
              } catch { /* global interceptor */ }
            }}
            okText="删除"
            cancelText="取消"
            okButtonProps={{ danger: true }}
          >
            <Button
              type="link"
              danger
              icon={<DeleteOutlined />}
              disabled={r.status === 'running' || r.status === 'pending'}
            >
              删除
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ]

  return (
    <>
      <BreadcrumbNav items={[
        { title: '项目列表', path: '/projects' },
        { title: project.name },
      ]} />
      <Typography.Title level={3} style={{ marginBottom: 8, marginTop: 0 }}>{project.name}</Typography.Title>
      {project.description && (
        <Typography.Paragraph type="secondary">{project.description}</Typography.Paragraph>
      )}

      {/* 配置摘要栏 */}
      <Card
        style={{ marginBottom: 24 }}
        styles={{ body: { padding: '16px 24px' } }}
        extra={
          <Tooltip title={!allReady ? `请先完成以下配置：${unreadyItems.join('、')}` : undefined}>
            <Button
              type="primary"
              icon={<PlayCircleOutlined />}
              disabled={!allReady}
              onClick={() => setModalOpen(true)}
            >
              发起批测
            </Button>
          </Tooltip>
        }
      >
        <Row gutter={16}>
          <Col span={6}>
            <ReadinessCard
              title="Agent 版本"
              icon={<ApiOutlined />}
              ready={readiness?.agent_version.ready ?? false}
              message={readiness?.agent_version.message ?? '加载中...'}
              onClick={() => navigate(`/projects/${id}/config?section=agent-versions`)}
            />
          </Col>
          <Col span={6}>
            <ReadinessCard
              title="测试用例"
              icon={<ExperimentOutlined />}
              ready={readiness?.test_case.ready ?? false}
              message={readiness?.test_case.message ?? '加载中...'}
              onClick={() => navigate(`/projects/${id}/config?section=test-cases`)}
            />
          </Col>
          <Col span={6}>
            <ReadinessCard
              title="裁判配置"
              icon={<AuditOutlined />}
              ready={readiness?.judge_config.ready ?? false}
              message={readiness?.judge_config.message ?? '加载中...'}
              onClick={() => navigate(`/projects/${id}/config?section=judge-config`)}
            />
          </Col>
          <Col span={6}>
            <ReadinessCard
              title="模型配置"
              icon={<RobotOutlined />}
              ready={readiness?.model_config_status.ready ?? false}
              message={readiness?.model_config_status.message ?? '加载中...'}
              onClick={() => navigate(`/projects/${id}/config?section=model-config`)}
            />
          </Col>
        </Row>
      </Card>

      {/* 批测记录列表 */}
      <Typography.Title level={5}>批测记录</Typography.Title>
      <Table
        columns={columns}
        dataSource={batches}
        rowKey="id"
        loading={batchLoading}
        pagination={false}
      />

      <CreateBatchModal
        projectId={id}
        open={modalOpen}
        onClose={() => setModalOpen(false)}
        onCreated={(batchId) => navigate(`/projects/${id}/batch-tests/${batchId}`)}
      />
    </>
  )
}
