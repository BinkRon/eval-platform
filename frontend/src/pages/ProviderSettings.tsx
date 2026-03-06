import { useState } from 'react'
import { Button, Card, Form, Input, Modal, Select, Space, Switch, Table, Tag, message } from 'antd'
import { PlusOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons'
import type { Provider } from '../api/providers'
import { useProviders, useCreateProvider, useUpdateProvider, useDeleteProvider } from '../hooks/useProviders'

export default function ProviderSettings() {
  const { data: providers, isLoading } = useProviders()
  const createMutation = useCreateProvider()
  const updateMutation = useUpdateProvider()
  const deleteMutation = useDeleteProvider()

  const [modalOpen, setModalOpen] = useState(false)
  const [editing, setEditing] = useState<Provider | null>(null)
  const [form] = Form.useForm()

  const openCreate = () => {
    setEditing(null)
    form.resetFields()
    setModalOpen(true)
  }

  const openEdit = (record: Provider) => {
    setEditing(record)
    form.setFieldsValue({
      provider_name: record.provider_name,
      base_url: record.base_url,
      available_models: record.available_models,
      is_active: record.is_active,
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

  const handleDelete = (record: Provider) => {
    Modal.confirm({
      title: `确认删除 ${record.provider_name}？`,
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
    { title: '厂商名称', dataIndex: 'provider_name', key: 'provider_name' },
    {
      title: 'API Key',
      key: 'api_key_set',
      render: (_: unknown, r: Provider) => (r.api_key_set ? <Tag color="green">已配置</Tag> : <Tag>未配置</Tag>),
    },
    { title: 'Base URL', dataIndex: 'base_url', key: 'base_url', render: (v: string | null) => v || '-' },
    {
      title: '可用模型',
      dataIndex: 'available_models',
      key: 'available_models',
      render: (v: string[] | null) => v?.join(', ') || '-',
    },
    {
      title: '状态',
      key: 'is_active',
      render: (_: unknown, r: Provider) => (r.is_active ? <Tag color="green">启用</Tag> : <Tag>停用</Tag>),
    },
    {
      title: '操作',
      key: 'actions',
      render: (_: unknown, r: Provider) => (
        <Space>
          <Button type="link" icon={<EditOutlined />} onClick={() => openEdit(r)}>编辑</Button>
          <Button type="link" danger icon={<DeleteOutlined />} onClick={() => handleDelete(r)}>删除</Button>
        </Space>
      ),
    },
  ]

  return (
    <Card
      title="全局模型管理"
      extra={<Button type="primary" icon={<PlusOutlined />} onClick={openCreate}>添加厂商</Button>}
    >
      <Table columns={columns} dataSource={providers} rowKey="id" loading={isLoading} pagination={false} />

      <Modal
        title={editing ? '编辑厂商' : '添加厂商'}
        open={modalOpen}
        onOk={handleSubmit}
        onCancel={() => setModalOpen(false)}
        confirmLoading={createMutation.isPending || updateMutation.isPending}
      >
        <Form form={form} layout="vertical" initialValues={{ is_active: true }}>
          <Form.Item
            name="provider_name"
            label="厂商名称"
            rules={[{ required: true, message: '请输入厂商名称' }]}
          >
            <Input placeholder="如 openai, anthropic" disabled={!!editing} />
          </Form.Item>
          <Form.Item name="api_key" label="API Key">
            <Input.Password placeholder={editing ? '留空则不修改' : '请输入 API Key'} />
          </Form.Item>
          <Form.Item name="base_url" label="Base URL">
            <Input placeholder="可选，自定义 API 地址" />
          </Form.Item>
          <Form.Item name="available_models" label="可用模型">
            <Select mode="tags" placeholder="输入模型名称后回车" />
          </Form.Item>
          <Form.Item name="is_active" label="启用" valuePropName="checked">
            <Switch />
          </Form.Item>
        </Form>
      </Modal>
    </Card>
  )
}
