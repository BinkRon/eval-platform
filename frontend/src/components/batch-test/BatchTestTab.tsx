import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Button, Form, InputNumber, Modal, Progress, Select, Space, Table, Tag, message } from 'antd'
import { PlayCircleOutlined, EyeOutlined } from '@ant-design/icons'
import type { BatchTest } from '../../api/batchTests'
import { useAgentVersions } from '../../hooks/useAgentVersions'
import { useBatchTests, useCreateBatchTest } from '../../hooks/useBatchTests'

const STATUS_MAP: Record<string, { color: string; label: string }> = {
  pending: { color: 'default', label: '等待中' },
  running: { color: 'processing', label: '运行中' },
  completed: { color: 'success', label: '已完成' },
  failed: { color: 'error', label: '失败' },
}

function BatchProgress({ batch }: { batch: BatchTest }) {
  const percent = batch.total_cases > 0 ? Math.round((batch.completed_cases / batch.total_cases) * 100) : 0

  if (batch.status !== 'running' && batch.status !== 'pending') {
    return <span>{batch.passed_cases}/{batch.total_cases} 通过</span>
  }

  return <Progress percent={percent} size="small" format={() => `${batch.completed_cases}/${batch.total_cases}`} />
}

export default function BatchTestTab({ projectId }: { projectId: string }) {
  const navigate = useNavigate()
  const { data: batches, isLoading } = useBatchTests(projectId)
  const { data: versions } = useAgentVersions(projectId)
  const createMutation = useCreateBatchTest(projectId)

  const [modalOpen, setModalOpen] = useState(false)
  const [form] = Form.useForm()

  const handleCreate = async () => {
    try {
      const values = await form.validateFields()
      await createMutation.mutateAsync(values)
      message.success('批测已发起')
      setModalOpen(false)
    } catch {
      // Global interceptor handles API errors
    }
  }

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
      title: '进度',
      key: 'progress',
      width: 200,
      render: (_: unknown, r: BatchTest) => <BatchProgress batch={r} />,
    },
    { title: '并发数', dataIndex: 'concurrency', key: 'concurrency', width: 80 },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (v: string) => new Date(v).toLocaleString(),
    },
    {
      title: '操作',
      key: 'actions',
      width: 80,
      render: (_: unknown, r: BatchTest) => (
        <Button
          type="link"
          icon={<EyeOutlined />}
          onClick={() => navigate(`/projects/${projectId}/batch-tests/${r.id}`)}
          disabled={r.status === 'pending'}
        >
          详情
        </Button>
      ),
    },
  ]

  return (
    <>
      <div style={{ marginBottom: 16 }}>
        <Button type="primary" icon={<PlayCircleOutlined />} onClick={() => { form.resetFields(); setModalOpen(true) }}>
          发起批测
        </Button>
      </div>
      <Table columns={columns} dataSource={batches} rowKey="id" loading={isLoading} pagination={false} />

      <Modal title="发起批测" open={modalOpen} onOk={handleCreate} onCancel={() => setModalOpen(false)} confirmLoading={createMutation.isPending}>
        <Form form={form} layout="vertical" initialValues={{ concurrency: 3 }}>
          <Form.Item name="agent_version_id" label="选择 Agent 版本" rules={[{ required: true, message: '请选择版本' }]}>
            <Select
              placeholder="选择要测试的 Agent 版本"
              options={(versions || []).map((v) => ({ value: v.id, label: v.name }))}
            />
          </Form.Item>
          <Form.Item name="concurrency" label="并发数">
            <InputNumber min={1} max={10} />
          </Form.Item>
        </Form>
      </Modal>
    </>
  )
}
