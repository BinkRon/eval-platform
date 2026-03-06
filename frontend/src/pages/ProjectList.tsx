import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Button, Card, Col, Form, Input, Modal, Row, Space, Typography, message } from 'antd'
import { PlusOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons'
import type { Project } from '../api/projects'
import { useProjects, useCreateProject, useUpdateProject, useDeleteProject } from '../hooks/useProjects'

export default function ProjectList() {
  const navigate = useNavigate()
  const { data: projects, isLoading } = useProjects()
  const createMutation = useCreateProject()
  const updateMutation = useUpdateProject()
  const deleteMutation = useDeleteProject()

  const [modalOpen, setModalOpen] = useState(false)
  const [editing, setEditing] = useState<Project | null>(null)
  const [form] = Form.useForm()

  const openCreate = () => {
    setEditing(null)
    form.resetFields()
    setModalOpen(true)
  }

  const openEdit = (e: React.MouseEvent, project: Project) => {
    e.stopPropagation()
    setEditing(project)
    form.setFieldsValue({ name: project.name, description: project.description })
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

  const handleDelete = (e: React.MouseEvent, project: Project) => {
    e.stopPropagation()
    Modal.confirm({
      title: `确认删除项目「${project.name}」？`,
      content: '删除后所有关联数据将一并删除，不可恢复。',
      onOk: async () => {
        await deleteMutation.mutateAsync(project.id)
        message.success('已删除')
      },
    })
  }

  return (
    <>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 16 }}>
        <Typography.Title level={3} style={{ margin: 0 }}>项目列表</Typography.Title>
        <Button type="primary" icon={<PlusOutlined />} onClick={openCreate}>新建项目</Button>
      </div>

      <Row gutter={[16, 16]}>
        {isLoading && <Col span={24}><Card loading /></Col>}
        {projects?.map((p) => (
          <Col key={p.id} xs={24} sm={12} lg={8} xl={6}>
            <Card
              hoverable
              onClick={() => navigate(`/projects/${p.id}`)}
              actions={[
                <EditOutlined key="edit" onClick={(e) => openEdit(e, p)} />,
                <DeleteOutlined key="delete" onClick={(e) => handleDelete(e, p)} />,
              ]}
            >
              <Card.Meta
                title={p.name}
                description={p.description || '暂无描述'}
              />
            </Card>
          </Col>
        ))}
      </Row>

      <Modal
        title={editing ? '编辑项目' : '新建项目'}
        open={modalOpen}
        onOk={handleSubmit}
        onCancel={() => setModalOpen(false)}
        confirmLoading={createMutation.isPending || updateMutation.isPending}
      >
        <Form form={form} layout="vertical">
          <Form.Item name="name" label="项目名称" rules={[{ required: true, message: '请输入项目名称' }]}>
            <Input placeholder="请输入项目名称" />
          </Form.Item>
          <Form.Item name="description" label="描述">
            <Input.TextArea rows={3} placeholder="可选" />
          </Form.Item>
        </Form>
      </Modal>
    </>
  )
}
