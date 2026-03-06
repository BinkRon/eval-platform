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

  const handleDelete = (record: TestCase) => {
    Modal.confirm({
      title: `确认删除用例「${record.name}」？`,
      onOk: async () => {
        await deleteMutation.mutateAsync(record.id)
        message.success('已删除')
      },
    })
  }

  const columns = [
    { title: '用例名称', dataIndex: 'name', key: 'name' },
    { title: '首条消息', dataIndex: 'first_message', key: 'first_message', ellipsis: true },
    { title: '最大轮数', dataIndex: 'max_rounds', key: 'max_rounds', width: 100 },
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
        <Form form={form} layout="vertical" initialValues={{ max_rounds: 20, sort_order: 0 }}>
          <Form.Item name="name" label="用例名称" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item name="first_message" label="首条消息" rules={[{ required: true }]}>
            <Input.TextArea rows={3} placeholder="对练机器人发给 Agent 的第一条消息" />
          </Form.Item>
          <Form.Item name="persona_background" label="用户画像背景">
            <Input.TextArea rows={2} placeholder="模拟用户的背景信息" />
          </Form.Item>
          <Form.Item name="persona_behavior" label="用户行为特征">
            <Input.TextArea rows={2} placeholder="模拟用户的行为偏好" />
          </Form.Item>
          <Form.Item name="max_rounds" label="最大对话轮数">
            <InputNumber min={1} max={50} />
          </Form.Item>
          <Form.Item name="sort_order" label="排序">
            <InputNumber min={0} />
          </Form.Item>
        </Form>
      </Modal>
    </>
  )
}
