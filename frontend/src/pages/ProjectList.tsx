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
              <div style={{ marginTop: 12, fontSize: 13, color: '#666', lineHeight: 1.8 }}>
                <div>Agent 版本数：{p.agent_version_count}</div>
                {p.latest_batch ? (
                  <div>
                    最近批测：{new Date(p.latest_batch.created_at).toLocaleDateString()} · {p.latest_batch.agent_version_name} · 通过率 {Math.round(p.latest_batch.pass_rate * 100)}%
                    {p.latest_batch.pass_rate_change != null && p.latest_batch.pass_rate_change !== 0 && (
                      <span style={{ color: p.latest_batch.pass_rate_change > 0 ? '#52c41a' : '#ff4d4f', marginLeft: 4 }}>
                        {p.latest_batch.pass_rate_change > 0 ? '↑' : '↓'}{Math.abs(p.latest_batch.pass_rate_change)}%
                      </span>
                    )}
                  </div>
                ) : (
                  <div>最近批测：—（未测）</div>
                )}
                <div>用例数：{p.test_case_count}　累计批测：{p.batch_test_count} 次</div>
              </div>
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
