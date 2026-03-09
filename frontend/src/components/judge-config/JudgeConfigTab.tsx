import { useCallback, useEffect, useRef } from 'react'
import { Button, Card, Form, Input, InputNumber, Select, Space, message } from 'antd'
import { PlusOutlined, MinusCircleOutlined } from '@ant-design/icons'
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

  useEffect(() => {
    if (config) {
      form.setFieldsValue({
        pass_threshold: Number(config.pass_threshold),
        checklist_items: config.checklist_items,
        eval_dimensions: config.eval_dimensions,
      })
      dataLoaded.current = true
    }
  }, [config, form])

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
      message.success('保存成功')
    } catch {
      // validation or API error handled by global interceptor
    }
  }

  if (isLoading) return <Card loading />

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

      <Button type="primary" onClick={handleSave} loading={updateMutation.isPending}>保存裁判配置</Button>
    </Form>
  )
}
