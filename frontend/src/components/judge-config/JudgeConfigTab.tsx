import { useCallback, useEffect, useRef, useState } from 'react'
import { Button, Card, Descriptions, Form, Input, InputNumber, Select, Space, Tag, message } from 'antd'
import { PlusOutlined, MinusCircleOutlined, EditOutlined } from '@ant-design/icons'
import { useJudgeConfig, useUpdateJudgeConfig } from '../../hooks/useJudgeConfig'

interface JudgeConfigTabProps {
  projectId: string
  onDirtyChange?: (dirty: boolean) => void
}

export default function JudgeConfigTab({ projectId, onDirtyChange }: JudgeConfigTabProps) {
  const { data: config, isLoading } = useJudgeConfig(projectId)
  const updateMutation = useUpdateJudgeConfig(projectId)
  const [form] = Form.useForm()
  const dataLoaded = useRef(false)
  const [editing, setEditing] = useState(false)

  useEffect(() => {
    if (config) {
      dataLoaded.current = false
      form.setFieldsValue({
        pass_threshold: config.pass_threshold,
        checklist_items: config.checklist_items,
        eval_dimensions: config.eval_dimensions,
      })
      dataLoaded.current = true
    }
  }, [config, form])

  // Auto-enter edit mode when no config exists yet (once only)
  const hasAutoEntered = useRef(false)
  useEffect(() => {
    if (!hasAutoEntered.current && config && !config.checklist_items.length && !config.eval_dimensions.length) {
      hasAutoEntered.current = true
      setEditing(true)
    }
  }, [config])

  const handleValuesChange = useCallback(() => {
    if (dataLoaded.current) {
      onDirtyChange?.(true)
    }
  }, [onDirtyChange])

  const handleSave = async () => {
    try {
      const values = await form.validateFields()
      values.checklist_items = (values.checklist_items || []).map((item: Record<string, unknown>, i: number) => ({
        ...item,
        sort_order: i,
      }))
      values.eval_dimensions = (values.eval_dimensions || []).map((dim: Record<string, unknown>, i: number) => ({
        ...dim,
        sort_order: i,
      }))
      await updateMutation.mutateAsync(values)
      onDirtyChange?.(false)
      setEditing(false)
      message.success('保存成功')
    } catch {
      // validation or API error handled by global interceptor
    }
  }

  const handleCancel = () => {
    if (config) {
      form.setFieldsValue({
        pass_threshold: config.pass_threshold,
        checklist_items: config.checklist_items,
        eval_dimensions: config.eval_dimensions,
      })
    }
    onDirtyChange?.(false)
    setEditing(false)
  }

  if (isLoading) return <Card loading />

  if (!editing && config) {
    return (
      <div>
        <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'flex-end' }}>
          <Button icon={<EditOutlined />} onClick={() => setEditing(true)}>编辑</Button>
        </div>

        <Descriptions column={1} bordered size="small" style={{ marginBottom: 16 }}>
          <Descriptions.Item label="通过阈值">{config.pass_threshold}</Descriptions.Item>
        </Descriptions>

        {config.checklist_items.length > 0 && (
          <Card title="Checklist 检查项" size="small" style={{ marginBottom: 16 }}>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
              {config.checklist_items.map((item) => (
                <Tag key={item.id} color={item.level === 'must' ? 'red' : 'orange'}>{item.content}</Tag>
              ))}
            </div>
          </Card>
        )}

        {config.eval_dimensions.length > 0 && (
          <Card title="Evaluation 评判维度" size="small">
            {config.eval_dimensions.map((dim) => (
              <Descriptions key={dim.id} column={2} size="small" bordered style={{ marginBottom: 8 }}>
                <Descriptions.Item label="维度名称" span={2}>{dim.name}</Descriptions.Item>
                {dim.description && <Descriptions.Item label="描述" span={2}>{dim.description}</Descriptions.Item>}
                {dim.level_3_desc && <Descriptions.Item label="3 分标准">{dim.level_3_desc}</Descriptions.Item>}
                {dim.level_2_desc && <Descriptions.Item label="2 分标准">{dim.level_2_desc}</Descriptions.Item>}
                {dim.level_1_desc && <Descriptions.Item label="1 分标准" span={2}>{dim.level_1_desc}</Descriptions.Item>}
              </Descriptions>
            ))}
          </Card>
        )}

        {config.checklist_items.length === 0 && config.eval_dimensions.length === 0 && (
          <Card size="small">
            <span style={{ color: '#999' }}>尚未配置裁判标准，点击"编辑"开始配置</span>
          </Card>
        )}
      </div>
    )
  }

  return (
    <Form form={form} layout="vertical" initialValues={{ pass_threshold: 2.0, checklist_items: [], eval_dimensions: [] }} onValuesChange={handleValuesChange}>
      <Form.Item name="pass_threshold" label="通过阈值（评判维度平均分 ≥ 该值即通过）">
        <InputNumber min={1} max={3} step={0.1} />
      </Form.Item>

      <Card title="Checklist 检查项" size="small" style={{ marginBottom: 16 }}>
        <Form.List name="checklist_items">
          {(fields, { add, remove }) => (
            <>
              {fields.map(({ key, name, ...rest }) => (
                <Space key={key} align="start" style={{ display: 'flex', marginBottom: 8 }}>
                  <Form.Item {...rest} name={[name, 'content']} rules={[{ required: true, message: '请输入内容' }]} style={{ flex: 1, minWidth: 300 }}>
                    <Input placeholder="检查项内容" />
                  </Form.Item>
                  <Form.Item {...rest} name={[name, 'level']} initialValue="must">
                    <Select style={{ width: 100 }} options={[{ value: 'must', label: '必须' }, { value: 'should', label: '应该' }]} />
                  </Form.Item>
                  <MinusCircleOutlined onClick={() => remove(name)} style={{ marginTop: 8 }} />
                </Space>
              ))}
              <Button type="dashed" onClick={() => add()} icon={<PlusOutlined />}>添加检查项</Button>
            </>
          )}
        </Form.List>
      </Card>

      <Card title="Evaluation 评判维度" size="small" style={{ marginBottom: 16 }}>
        <Form.List name="eval_dimensions">
          {(fields, { add, remove }) => (
            <>
              {fields.map(({ key, name, ...rest }) => (
                <Card key={key} size="small" style={{ marginBottom: 8 }} extra={<MinusCircleOutlined onClick={() => remove(name)} />}>
                  <Form.Item {...rest} name={[name, 'name']} label="维度名称" rules={[{ required: true }]}>
                    <Input placeholder="如：专业度" />
                  </Form.Item>
                  <Form.Item {...rest} name={[name, 'description']} label="维度描述">
                    <Input.TextArea rows={1} />
                  </Form.Item>
                  <Form.Item {...rest} name={[name, 'level_3_desc']} label="3 分标准">
                    <Input.TextArea rows={1} />
                  </Form.Item>
                  <Form.Item {...rest} name={[name, 'level_2_desc']} label="2 分标准">
                    <Input.TextArea rows={1} />
                  </Form.Item>
                  <Form.Item {...rest} name={[name, 'level_1_desc']} label="1 分标准">
                    <Input.TextArea rows={1} />
                  </Form.Item>
                </Card>
              ))}
              <Button type="dashed" onClick={() => add()} icon={<PlusOutlined />}>添加评判维度</Button>
            </>
          )}
        </Form.List>
      </Card>

      <Space>
        <Button type="primary" onClick={handleSave} loading={updateMutation.isPending}>保存</Button>
        <Button onClick={handleCancel}>取消</Button>
      </Space>
    </Form>
  )
}
