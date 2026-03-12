import { useState } from 'react'
import { Button, Form, Input, InputNumber, Modal, Space, Table, message } from 'antd'
import { PlusOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons'
import type { TestCase } from '../../api/testCases'
import { useTestCases, useCreateTestCase, useUpdateTestCase, useDeleteTestCase } from '../../hooks/useTestCases'

export default function TestCaseTab({ projectId }: { projectId: string }) {
  const { data: cases, isLoading } = useTestCases(projectId)
  const createMutation = useCreateTestCase(projectId)
  const updateMutation = useUpdateTestCase(projectId)
  const deleteMutation = useDeleteTestCase(projectId)

  const [modalOpen, setModalOpen] = useState(false)
  const [editing, setEditing] = useState<TestCase | null>(null)
  const [form] = Form.useForm()

  const openCreate = () => {
    setEditing(null)
    form.resetFields()
    setModalOpen(true)
  }

  const openEdit = (record: TestCase) => {
    setEditing(record)
    form.setFieldsValue({
      name: record.name,
      sparring_prompt: record.sparring_prompt,
      first_message: record.first_message,
      max_rounds: record.max_rounds,
      sort_order: record.sort_order,
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

  const handleDelete = (record: TestCase) => {
    Modal.confirm({
      title: `确认删除用例「${record.name}」？`,
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
    { title: '用例名称', dataIndex: 'name', key: 'name' },
    {
      title: '角色描述',
      dataIndex: 'sparring_prompt',
      key: 'sparring_prompt',
      ellipsis: true,
      render: (text: string) => text ? text.slice(0, 40) + (text.length > 40 ? '…' : '') : '—',
    },
    {
      title: '操作',
      key: 'actions',
      width: 150,
      render: (_: unknown, r: TestCase) => (
        <Space>
          <Button type="link" icon={<EditOutlined />} onClick={() => openEdit(r)}>编辑</Button>
          <Button type="link" danger icon={<DeleteOutlined />} onClick={() => handleDelete(r)}>删除</Button>
        </Space>
      ),
    },
  ]

  return (
    <>
      <div style={{ marginBottom: 16 }}>
        <Button type="primary" icon={<PlusOutlined />} onClick={openCreate}>添加用例</Button>
      </div>
      <Table columns={columns} dataSource={cases} rowKey="id" loading={isLoading} pagination={false} />

      <Modal
        title={editing ? '编辑测试用例' : '添加测试用例'}
        open={modalOpen}
        onOk={handleSubmit}
        onCancel={() => setModalOpen(false)}
        width={640}
        confirmLoading={createMutation.isPending || updateMutation.isPending}
      >
        <Form form={form} layout="vertical" initialValues={{ max_rounds: 50, sort_order: 0 }}>
          <Form.Item name="name" label="用例名称" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item name="sparring_prompt" label="角色描述" rules={[{ required: true }]}
            extra="支持 markdown 格式。此内容将作为对练模型的角色扮演指令。">
            <Input.TextArea rows={6} placeholder="描述对练机器人的角色身份、性格、行为规则等" />
          </Form.Item>
          <Form.Item name="first_message" label="首轮发言"
            extra="对练机器人的开场白，默认为"喂？"">
            <Input placeholder="喂？" />
          </Form.Item>
          <Form.Item name="max_rounds" label="最大轮次（兜底）"
            extra="系统默认 50 轮，仅在特殊场景需要调整">
            <InputNumber min={3} max={100} />
          </Form.Item>
          <Form.Item name="sort_order" label="排序">
            <InputNumber min={0} />
          </Form.Item>
        </Form>
      </Modal>
    </>
  )
}
