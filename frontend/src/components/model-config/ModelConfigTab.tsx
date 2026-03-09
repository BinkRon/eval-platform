import { useCallback, useEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import { Alert, Button, Card, Col, Descriptions, Form, Input, InputNumber, Row, Select, Space, message } from 'antd'
import { EditOutlined } from '@ant-design/icons'
import { useModelConfig, useUpdateModelConfig, useModelOptions } from '../../hooks/useModelConfig'

interface ModelConfigTabProps {
  projectId: string
  onDirtyChange?: (dirty: boolean) => void
}

export default function ModelConfigTab({ projectId, onDirtyChange }: ModelConfigTabProps) {
  const { data: config, isLoading } = useModelConfig(projectId)
  const { data: modelOptions, isLoading: optionsLoading } = useModelOptions()
  const updateMutation = useUpdateModelConfig(projectId)
  const [form] = Form.useForm()
  const dataLoaded = useRef(false)
  const [editing, setEditing] = useState(false)

  useEffect(() => {
    if (config) {
      dataLoaded.current = false
      form.setFieldsValue(config)
      dataLoaded.current = true
    }
  }, [config, form])

  // Auto-enter edit mode when config has no models configured (once only)
  const hasAutoEntered = useRef(false)
  useEffect(() => {
    if (!hasAutoEntered.current && config && !config.sparring_provider && !config.judge_provider) {
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
      form.setFieldsValue(config)
    }
    onDirtyChange?.(false)
    setEditing(false)
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

  const noProviders = !optionsLoading && providerOptions.length === 0

  if (!editing && config) {
    const hasConfig = config.sparring_provider || config.judge_provider
    return (
      <div>
        <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'flex-end' }}>
          <Button icon={<EditOutlined />} onClick={() => setEditing(true)}>编辑</Button>
        </div>

        {hasConfig ? (
          <Row gutter={24}>
            <Col span={12}>
              <Card title="对练模型" size="small">
                <Descriptions column={1} size="small">
                  <Descriptions.Item label="厂商">{config.sparring_provider || '-'}</Descriptions.Item>
                  <Descriptions.Item label="模型">{config.sparring_model || '-'}</Descriptions.Item>
                  <Descriptions.Item label="Temperature">{config.sparring_temperature ?? '-'}</Descriptions.Item>
                  <Descriptions.Item label="Max Tokens">{config.sparring_max_tokens ?? '-'}</Descriptions.Item>
                  {config.sparring_system_prompt && (
                    <Descriptions.Item label="System Prompt">
                      <div style={{ whiteSpace: 'pre-wrap', maxHeight: 100, overflow: 'auto' }}>{config.sparring_system_prompt}</div>
                    </Descriptions.Item>
                  )}
                </Descriptions>
              </Card>
            </Col>
            <Col span={12}>
              <Card title="裁判模型" size="small">
                <Descriptions column={1} size="small">
                  <Descriptions.Item label="厂商">{config.judge_provider || '-'}</Descriptions.Item>
                  <Descriptions.Item label="模型">{config.judge_model || '-'}</Descriptions.Item>
                  <Descriptions.Item label="Temperature">{config.judge_temperature ?? '-'}</Descriptions.Item>
                  <Descriptions.Item label="Max Tokens">{config.judge_max_tokens ?? '-'}</Descriptions.Item>
                  {config.judge_system_prompt && (
                    <Descriptions.Item label="System Prompt">
                      <div style={{ whiteSpace: 'pre-wrap', maxHeight: 100, overflow: 'auto' }}>{config.judge_system_prompt}</div>
                    </Descriptions.Item>
                  )}
                </Descriptions>
              </Card>
            </Col>
          </Row>
        ) : (
          <Card size="small">
            <span style={{ color: '#999' }}>尚未配置模型，点击"编辑"开始配置</span>
          </Card>
        )}
      </div>
    )
  }

  return (
    <Form form={form} layout="vertical" onValuesChange={handleValuesChange}>
      {noProviders && (
        <Alert
          type="warning"
          showIcon
          style={{ marginBottom: 16 }}
          message="尚未配置模型供应商"
          description={
            <span>
              请先前往 <Link to="/settings/providers">模型管理</Link> 添加供应商并配置 API Key，然后再选择模型。
            </span>
          }
        />
      )}
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
        <Space>
          <Button type="primary" onClick={handleSave} loading={updateMutation.isPending}>保存</Button>
          <Button onClick={handleCancel}>取消</Button>
        </Space>
      </div>
    </Form>
  )
}
