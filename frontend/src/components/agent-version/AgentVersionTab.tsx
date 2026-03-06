import { useState } from 'react'
import { Button, Form, Input, Modal, Select, Space, Switch, Table, Tag, message } from 'antd'
import { PlusOutlined, EditOutlined, DeleteOutlined, ApiOutlined } from '@ant-design/icons'
import { useQueryClient } from '@tanstack/react-query'
import { agentVersionApi, type AgentVersion } from '../../api/agentVersions'
import {
  useAgentVersions,
  useCreateAgentVersion,
  useUpdateAgentVersion,
  useDeleteAgentVersion,
} from '../../hooks/useAgentVersions'

const STATUS_MAP: Record<string, { color: string; label: string }> = {
  untested: { color: 'default', label: '未测试' },
  success: { color: 'green', label: '连接成功' },
  failed: { color: 'red', label: '连接失败' },
}

export default function AgentVersionTab({ projectId }: { projectId: string }) {
  const qc = useQueryClient()
  const { data: versions, isLoading } = useAgentVersions(projectId)
  const createMutation = useCreateAgentVersion(projectId)
  const updateMutation = useUpdateAgentVersion(projectId)
  const deleteMutation = useDeleteAgentVersion(projectId)

  const [testing, setTesting] = useState<string | null>(null)
  const [modalOpen, setModalOpen] = useState(false)
  const [editing, setEditing] = useState<AgentVersion | null>(null)
  const [form] = Form.useForm()

  const openCreate = () => {
    setEditing(null)
    form.resetFields()
    setModalOpen(true)
  }

  const openEdit = (record: AgentVersion) => {
    setEditing(record)
    form.setFieldsValue(record)
    setModalOpen(true)
  }

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields()
      if (editing) {
        await updateMutation.mutateAsync({ id: editing.id, data: values })
        message.success('更新成功')
      } else {
        await createMutation.mutateAsync(values)
        message.success('创建成功')
      }
      setModalOpen(false)
    } catch {
      // Global interceptor handles API errors
    }
  }

  const handleTest = async (record: AgentVersion) => {
    setTesting(record.id)
    try {
      const result = await agentVersionApi.test(projectId, record.id)
      if (result.status === 'success') {
        message.success(`连接成功：${result.reply?.slice(0, 50)}`)
      } else {
        message.error(`连接失败：${result.error}`)
      }
      qc.invalidateQueries({ queryKey: ['agent-versions', projectId] })
    } catch {
      message.error('连接测试失败')
    } finally {
      setTesting(null)
    }
  }

  const handleDelete = (record: AgentVersion) => {
    Modal.confirm({
      title: `确认删除「${record.name}」？`,
      onOk: async () => {
        await deleteMutation.mutateAsync(record.id)
        message.success('已删除')
      },
    })
  }

  const columns = [
    { title: '版本名称', dataIndex: 'name', key: 'name' },
    { title: 'Endpoint', dataIndex: 'endpoint', key: 'endpoint', render: (v: string | null) => v || '-' },
    { title: '方法', dataIndex: 'method', key: 'method', width: 80 },
    {
      title: '连接状态',
      key: 'connection_status',
      width: 100,
      render: (_: unknown, r: AgentVersion) => {
        const s = STATUS_MAP[r.connection_status] || STATUS_MAP.untested
        return <Tag color={s.color}>{s.label}</Tag>
      },
    },
    {
      title: '操作',
      key: 'actions',
      width: 150,
      render: (_: unknown, r: AgentVersion) => (
        <Space>
          <Button type="link" icon={<ApiOutlined />} onClick={() => handleTest(r)} loading={testing === r.id} disabled={!r.endpoint}>测试</Button>
          <Button type="link" icon={<EditOutlined />} onClick={() => openEdit(r)}>编辑</Button>
          <Button type="link" danger icon={<DeleteOutlined />} onClick={() => handleDelete(r)}>删除</Button>
        </Space>
      ),
    },
  ]

  return (
    <>
      <div style={{ marginBottom: 16 }}>
        <Button type="primary" icon={<PlusOutlined />} onClick={openCreate}>添加版本</Button>
      </div>
      <Table columns={columns} dataSource={versions} rowKey="id" loading={isLoading} pagination={false} />

      <Modal
        title={editing ? '编辑 Agent 版本' : '添加 Agent 版本'}
        open={modalOpen}
        onOk={handleSubmit}
        onCancel={() => setModalOpen(false)}
        width={640}
        confirmLoading={createMutation.isPending || updateMutation.isPending}
      >
        <Form form={form} layout="vertical" initialValues={{ method: 'POST', response_format: 'json', has_end_signal: false }}>
          <Form.Item name="name" label="版本名称" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item name="description" label="描述">
            <Input.TextArea rows={2} />
          </Form.Item>
          <Form.Item name="endpoint" label="API Endpoint">
            <Input placeholder="https://your-agent.com/api/chat" />
          </Form.Item>
          <Form.Item name="method" label="请求方法">
            <Select options={[{ value: 'POST' }, { value: 'GET' }]} />
          </Form.Item>
          <Form.Item name="response_format" label="响应格式">
            <Select options={[{ value: 'json', label: 'JSON' }, { value: 'sse', label: 'SSE (Server-Sent Events)' }]} />
          </Form.Item>
          <Form.Item name="auth_type" label="认证方式">
            <Select allowClear options={[{ value: 'bearer', label: 'Bearer Token' }, { value: 'header', label: '自定义 Header' }]} />
          </Form.Item>
          <Form.Item name="auth_token" label="认证令牌">
            <Input.Password />
          </Form.Item>
          <Form.Item name="request_template" label="请求模板 (JSON)">
            <Input.TextArea rows={4} placeholder='{"message": "{{message}}", "session_id": "{{session_id}}"}' />
          </Form.Item>
          <Form.Item name="response_path" label="响应解析路径 (JSONPath)">
            <Input placeholder="$.data.reply" />
          </Form.Item>
          <Form.Item name="has_end_signal" label="结束信号" valuePropName="checked">
            <Switch />
          </Form.Item>
          <Form.Item name="end_signal_path" label="结束信号路径">
            <Input placeholder="$.data.is_end" />
          </Form.Item>
          <Form.Item name="end_signal_value" label="结束信号值">
            <Input placeholder="true" />
          </Form.Item>
        </Form>
      </Modal>
    </>
  )
}
