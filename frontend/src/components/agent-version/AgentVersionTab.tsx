import { useState } from 'react'
import { Button, Col, Divider, Form, Input, Modal, Row, Select, Space, Switch, Table, Tag, message } from 'antd'
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
  const [testingUnsaved, setTestingUnsaved] = useState(false)
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
    form.setFieldsValue({
      name: record.name,
      description: record.description,
      endpoint: record.endpoint,
      method: record.method,
      response_format: record.response_format,
      auth_type: record.auth_type,
      auth_token: undefined,
      request_template: record.request_template,
      response_path: record.response_path,
      has_end_signal: record.has_end_signal,
      end_signal_path: record.end_signal_path,
      end_signal_value: record.end_signal_value,
    })
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

  const handleTestUnsaved = async () => {
    try {
      const values = await form.validateFields()
      setTestingUnsaved(true)
      const result = await agentVersionApi.testUnsaved(projectId, values)
      if (result.status === 'success') {
        message.success(`连接成功：${result.reply?.slice(0, 50)}`)
      } else {
        message.error(`连接失败：${result.error}`)
      }
    } catch {
      // validation error or network error
    } finally {
      setTestingUnsaved(false)
    }
  }

  const handleDelete = (record: AgentVersion) => {
    Modal.confirm({
      title: `确认删除「${record.name}」？`,
      onOk: async () => {
        try {
          await deleteMutation.mutateAsync(record.id)
          message.success('已删除')
        } catch {
          // error handled by global interceptor
        }
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
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <span style={{ fontWeight: 500 }}>Agent 版本</span>
        <Button type="primary" icon={<PlusOutlined />} onClick={openCreate}>添加版本</Button>
      </div>
      <Table columns={columns} dataSource={versions} rowKey="id" loading={isLoading} pagination={false} />

      <Modal
        title={editing ? '编辑 Agent 版本' : '添加 Agent 版本'}
        open={modalOpen}
        onCancel={() => setModalOpen(false)}
        width={640}
        footer={
          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            <Button icon={<ApiOutlined />} onClick={handleTestUnsaved} loading={testingUnsaved}>测试连接</Button>
            <Space>
              <Button onClick={() => setModalOpen(false)}>取消</Button>
              <Button type="primary" onClick={handleSubmit} loading={createMutation.isPending || updateMutation.isPending}>确定</Button>
            </Space>
          </div>
        }
      >
        <Form form={form} layout="vertical" initialValues={{ method: 'POST', response_format: 'json', has_end_signal: false }}>
          <Divider titlePlacement="left" style={{ marginTop: 0 }}>基础信息</Divider>
          <Form.Item name="name" label="版本名称" rules={[{ required: true, message: '请输入版本名称' }]}>
            <Input placeholder="如：v1.0、生产环境" />
          </Form.Item>
          <Form.Item name="description" label="描述">
            <Input.TextArea rows={2} placeholder="版本说明，便于区分不同版本" />
          </Form.Item>

          <Divider titlePlacement="left">连接配置</Divider>
          <Form.Item name="endpoint" label="API Endpoint" rules={[{ required: true, message: '请输入 API 地址' }]}>
            <Input placeholder="https://your-agent.com/api/chat" />
          </Form.Item>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="method" label="请求方法">
                <Select options={[{ value: 'POST' }, { value: 'GET' }]} />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="response_format" label="响应格式">
                <Select options={[{ value: 'json', label: 'JSON' }, { value: 'sse', label: 'SSE (流式)' }]} />
              </Form.Item>
            </Col>
          </Row>
          <Form.Item name="auth_type" label="认证方式">
            <Select allowClear placeholder="无需认证" options={[{ value: 'bearer', label: 'Bearer Token' }, { value: 'header', label: '自定义 Header' }]} />
          </Form.Item>
          <Form.Item noStyle shouldUpdate={(prev, cur) => prev.auth_type !== cur.auth_type}>
            {({ getFieldValue }) =>
              getFieldValue('auth_type') ? (
                <Form.Item name="auth_token" label={getFieldValue('auth_type') === 'bearer' ? 'Token' : 'Header 值'}>
                  <Input.Password placeholder={editing?.auth_token_set ? '已配置，留空表示不修改' : undefined} />
                </Form.Item>
              ) : null
            }
          </Form.Item>

          <Divider titlePlacement="left">协议配置</Divider>
          <Form.Item name="request_template" label="请求模板 (JSON)" tooltip="使用 {{message}} 和 {{session_id}} 作为占位符">
            <Input.TextArea rows={3} placeholder='{"message": "{{message}}", "session_id": "{{session_id}}"}' />
          </Form.Item>
          <Form.Item name="response_path" label="响应解析路径 (JSONPath)" tooltip="从响应 JSON 中提取回复文本的路径">
            <Input placeholder="$.data.reply" />
          </Form.Item>
          <Form.Item name="has_end_signal" label="结束信号" valuePropName="checked" tooltip="Agent 是否通过特定字段标记对话结束">
            <Switch />
          </Form.Item>
          <Form.Item noStyle shouldUpdate={(prev, cur) => prev.has_end_signal !== cur.has_end_signal}>
            {({ getFieldValue }) =>
              getFieldValue('has_end_signal') ? (
                <Row gutter={16}>
                  <Col span={14}>
                    <Form.Item name="end_signal_path" label="信号路径" rules={[{ required: true, message: '请输入信号路径' }]}>
                      <Input placeholder="$.data.is_end" />
                    </Form.Item>
                  </Col>
                  <Col span={10}>
                    <Form.Item name="end_signal_value" label="信号值" rules={[{ required: true, message: '请输入信号值' }]}>
                      <Input placeholder="true" />
                    </Form.Item>
                  </Col>
                </Row>
              ) : null
            }
          </Form.Item>
        </Form>
      </Modal>
    </>
  )
}
