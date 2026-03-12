import { useCallback, useEffect, useRef, useState } from 'react'
import { Button, Card, Form, Input, InputNumber, Select, Space, Table, Tag, Typography, message } from 'antd'
import { PlusOutlined, MinusCircleOutlined, EditOutlined } from '@ant-design/icons'
import { useJudgeConfig, useUpdateJudgeConfig } from '../../hooks/useJudgeConfig'
import type { ChecklistItem, EvalDimension } from '../../types/judgeConfig'

const { Text, Paragraph } = Typography

interface JudgeConfigTabProps {
  projectId: string
  onDirtyChange?: (dirty: boolean) => void
}

/* ── 查看态：Checklist Table ── */

const checklistColumns = [
  {
    title: '#',
    width: 50,
    render: (_: unknown, __: unknown, index: number) => index + 1,
  },
  {
    title: '检查内容',
    dataIndex: 'content',
    key: 'content',
  },
  {
    title: '级别',
    dataIndex: 'level',
    key: 'level',
    width: 80,
    render: (level: string) => (
      <Tag color={level === 'must' ? 'red' : 'orange'}>
        {level === 'must' ? '必须' : '应该'}
      </Tag>
    ),
  },
]

/* ── 查看态：评判维度 Card ── */

function DimensionCard({ dim }: { dim: EvalDimension }) {
  const previewLines = dim.judge_prompt_segment
    ? dim.judge_prompt_segment.split('\n').slice(0, 2).join('\n')
    : ''

  return (
    <Card size="small" style={{ marginBottom: 12 }}>
      <div style={{ marginBottom: 8 }}>
        <Text strong>{dim.name}</Text>
      </div>
      {previewLines && (
        <Paragraph type="secondary" style={{ margin: 0, whiteSpace: 'pre-wrap' }}>
          {previewLines}{dim.judge_prompt_segment.split('\n').length > 2 ? '\n…' : ''}
        </Paragraph>
      )}
    </Card>
  )
}

/* ── 查看态 ── */

function JudgeConfigView({
  passThreshold,
  checklistItems,
  evalDimensions,
  onEdit,
}: {
  passThreshold: number
  checklistItems: ChecklistItem[]
  evalDimensions: EvalDimension[]
  onEdit: () => void
}) {
  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: 16 }}>
        <Button icon={<EditOutlined />} onClick={onEdit}>编辑</Button>
      </div>

      <div style={{ marginBottom: 20 }}>
        <Text type="secondary">通过阈值　</Text>
        <Text strong>{passThreshold}</Text>
      </div>

      <div style={{ marginBottom: 20 }}>
        <Text type="secondary" style={{ display: 'block', marginBottom: 8 }}>
          Checklist 检查项（{checklistItems.length} 条）
        </Text>
        {checklistItems.length > 0 ? (
          <Table
            size="small"
            dataSource={checklistItems}
            columns={checklistColumns}
            pagination={false}
            rowKey={(_, i) => String(i)}
          />
        ) : (
          <Text type="secondary">暂无检查项</Text>
        )}
      </div>

      <div>
        <Text type="secondary" style={{ display: 'block', marginBottom: 8 }}>
          评判维度（{evalDimensions.length} 个）
        </Text>
        {evalDimensions.length > 0
          ? evalDimensions.map((dim, i) => <DimensionCard key={dim.id || i} dim={dim} />)
          : <Text type="secondary">暂无评判维度</Text>
        }
      </div>
    </div>
  )
}

/* ── 编辑态 ── */

function JudgeConfigEdit({
  form,
  saving,
  onSave,
  onCancel,
  onValuesChange,
}: {
  form: ReturnType<typeof Form.useForm>[0]
  saving: boolean
  onSave: () => void
  onCancel: () => void
  onValuesChange: () => void
}) {
  return (
    <Form form={form} layout="vertical" onValuesChange={onValuesChange}>
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
                  <Form.Item {...rest} name={[name, 'judge_prompt_segment']} label="评判指引"
                    rules={[{ required: true, message: '请输入评判指引' }]}
                    extra="支持 markdown 格式。可包含评分等级定义、边界情况说明、正反例等。">
                    <Input.TextArea rows={4} placeholder="评判该维度的指引内容，包含评分标准等" />
                  </Form.Item>
                </Card>
              ))}
              <Button type="dashed" onClick={() => add()} icon={<PlusOutlined />}>添加评判维度</Button>
            </>
          )}
        </Form.List>
      </Card>

      <Space>
        <Button type="primary" onClick={onSave} loading={saving}>保存裁判配置</Button>
        <Button onClick={onCancel}>取消</Button>
      </Space>
    </Form>
  )
}

/* ── 主组件 ── */

export default function JudgeConfigTab({ projectId, onDirtyChange }: JudgeConfigTabProps) {
  const { data: config, isLoading } = useJudgeConfig(projectId)
  const updateMutation = useUpdateJudgeConfig(projectId)
  const [form] = Form.useForm()
  const [editing, setEditing] = useState(false)
  const hasAutoEntered = useRef(false)
  const dataLoaded = useRef(false)

  // 首次无数据自动进入编辑态
  useEffect(() => {
    if (config && !hasAutoEntered.current) {
      hasAutoEntered.current = true
      const empty = config.checklist_items.length === 0 && config.eval_dimensions.length === 0
      if (empty) {
        setEditing(true)
        form.setFieldsValue({
          pass_threshold: Number(config.pass_threshold),
          checklist_items: [],
          eval_dimensions: [],
        })
        dataLoaded.current = true
      }
    }
  }, [config, form])

  const enterEdit = useCallback(() => {
    if (!config) return
    form.setFieldsValue({
      pass_threshold: Number(config.pass_threshold),
      checklist_items: config.checklist_items,
      eval_dimensions: config.eval_dimensions,
    })
    dataLoaded.current = true
    setEditing(true)
  }, [config, form])

  const cancelEdit = useCallback(() => {
    setEditing(false)
    onDirtyChange?.(false)
  }, [onDirtyChange])

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

  if (isLoading) return <Card loading />

  if (editing) {
    return (
      <JudgeConfigEdit
        form={form}
        saving={updateMutation.isPending}
        onSave={handleSave}
        onCancel={cancelEdit}
        onValuesChange={handleValuesChange}
      />
    )
  }

  return (
    <JudgeConfigView
      passThreshold={Number(config?.pass_threshold ?? 2.0)}
      checklistItems={config?.checklist_items ?? []}
      evalDimensions={config?.eval_dimensions ?? []}
      onEdit={enterEdit}
    />
  )
}
