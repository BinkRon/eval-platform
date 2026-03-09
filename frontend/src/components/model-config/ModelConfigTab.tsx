import { useCallback, useEffect, useRef } from 'react'
import { Button, Card, Col, Form, Input, InputNumber, Row, Select, message } from 'antd'
import { useModelConfig, useUpdateModelConfig, useModelOptions } from '../../hooks/useModelConfig'

interface ModelConfigTabProps {
  projectId: string
  onDirtyChange?: (dirty: boolean) => void
}

export default function ModelConfigTab({ projectId, onDirtyChange }: ModelConfigTabProps) {
  const { data: config, isLoading } = useModelConfig(projectId)
  const { data: modelOptions } = useModelOptions()
  const updateMutation = useUpdateModelConfig(projectId)
  const [form] = Form.useForm()
  const dataLoaded = useRef(false)

  useEffect(() => {
    if (config) {
      form.setFieldsValue(config)
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
      await updateMutation.mutateAsync(values)
      onDirtyChange?.(false)
      message.success('保存成功')
    } catch {
      // validation or API error handled by global interceptor
    }
  }

  // Group models by provider
  const providerModels = (modelOptions || []).reduce<Record<string, string[]>>((acc, opt) => {
    if (!acc[opt.provider]) acc[opt.provider] = []
    acc[opt.provider].push(opt.model)
    return acc
  }, {})

  const providerOptions = Object.keys(providerModels).map((p) => ({ value: p, label: p }))

  const getModelOptions = (provider: string | null) =>
    provider && providerModels[provider]
      ? providerModels[provider].map((m) => ({ value: m, label: m }))
      : []

  if (isLoading) return <Card loading />

  return (
    <Form form={form} layout="vertical" onValuesChange={handleValuesChange}>
      <Row gutter={24}>
        <Col span={12}>
          <Card title="对练模型配置" size="small">
            <Form.Item name="sparring_provider" label="厂商">
              <Select options={providerOptions} allowClear placeholder="选择厂商" onChange={() => form.setFieldValue('sparring_model', null)} />
            </Form.Item>
            <Form.Item noStyle shouldUpdate={(prev, cur) => prev.sparring_provider !== cur.sparring_provider}>
              {({ getFieldValue }) => (
                <Form.Item name="sparring_model" label="模型">
                  <Select options={getModelOptions(getFieldValue('sparring_provider'))} allowClear placeholder="选择模型" />
                </Form.Item>
              )}
            </Form.Item>
            <Form.Item name="sparring_temperature" label="Temperature">
              <InputNumber min={0} max={2} step={0.1} style={{ width: '100%' }} />
            </Form.Item>
            <Form.Item name="sparring_max_tokens" label="Max Tokens">
              <InputNumber min={1} max={16384} style={{ width: '100%' }} />
            </Form.Item>
            <Form.Item name="sparring_system_prompt" label="System Prompt">
              <Input.TextArea rows={4} />
            </Form.Item>
          </Card>
        </Col>
        <Col span={12}>
          <Card title="裁判模型配置" size="small">
            <Form.Item name="judge_provider" label="厂商">
              <Select options={providerOptions} allowClear placeholder="选择厂商" onChange={() => form.setFieldValue('judge_model', null)} />
            </Form.Item>
            <Form.Item noStyle shouldUpdate={(prev, cur) => prev.judge_provider !== cur.judge_provider}>
              {({ getFieldValue }) => (
                <Form.Item name="judge_model" label="模型">
                  <Select options={getModelOptions(getFieldValue('judge_provider'))} allowClear placeholder="选择模型" />
                </Form.Item>
              )}
            </Form.Item>
            <Form.Item name="judge_temperature" label="Temperature">
              <InputNumber min={0} max={2} step={0.1} style={{ width: '100%' }} />
            </Form.Item>
            <Form.Item name="judge_max_tokens" label="Max Tokens">
              <InputNumber min={1} max={16384} style={{ width: '100%' }} />
            </Form.Item>
            <Form.Item name="judge_system_prompt" label="System Prompt">
              <Input.TextArea rows={4} />
            </Form.Item>
          </Card>
        </Col>
      </Row>
      <div style={{ marginTop: 16 }}>
        <Button type="primary" onClick={handleSave} loading={updateMutation.isPending}>保存模型配置</Button>
      </div>
    </Form>
  )
}
