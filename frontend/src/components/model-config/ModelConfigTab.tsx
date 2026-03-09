import { useCallback, useEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import { Alert, Button, Card, Form, Input, InputNumber, Select, Space, Typography, message } from 'antd'
import { EditOutlined } from '@ant-design/icons'
import { useModelConfig, useUpdateModelConfig, useModelOptions } from '../../hooks/useModelConfig'
import type { ModelConfig, ModelConfigUpdate } from '../../types/modelConfig'

const { Text, Paragraph } = Typography

interface ModelConfigTabProps {
  projectId: string
  onDirtyChange?: (dirty: boolean) => void
}

/* ── 查看态：单个模型 Card ── */

function ModelCardView({
  title,
  provider,
  model,
  temperature,
  maxTokens,
  systemPrompt,
  onEdit,
}: {
  title: string
  provider: string | null
  model: string | null
  temperature: number | null
  maxTokens: number | null
  systemPrompt: string | null
  onEdit: () => void
}) {
  const configured = !!provider

  return (
    <Card size="small" title={title} extra={<Button icon={<EditOutlined />} onClick={onEdit}>编辑</Button>}>
      {!configured ? (
        <Text type="secondary">未配置</Text>
      ) : (
        <>
          <div style={{ marginBottom: 8 }}>
            <Text type="secondary">厂商　</Text>
            <Text strong>{provider}</Text>
          </div>
          <div style={{ marginBottom: 8 }}>
            <Text type="secondary">模型　</Text>
            <Text strong>{model ?? '—'}</Text>
          </div>
          <div style={{ display: 'flex', gap: 32, marginBottom: 8 }}>
            <div>
              <Text type="secondary">Temperature　</Text>
              <Text strong>{temperature ?? '—'}</Text>
            </div>
            <div>
              <Text type="secondary">Max Tokens　</Text>
              <Text strong>{maxTokens ?? '—'}</Text>
            </div>
          </div>
          {systemPrompt && (
            <div>
              <Text type="secondary" style={{ display: 'block', marginBottom: 4 }}>System Prompt</Text>
              <div style={{ background: '#f5f5f5', borderRadius: 6, padding: '8px 12px' }}>
                <Paragraph ellipsis={{ rows: 4, expandable: true, symbol: '展开' }} style={{ margin: 0, whiteSpace: 'pre-wrap' }}>
                  {systemPrompt}
                </Paragraph>
              </div>
            </div>
          )}
        </>
      )}
    </Card>
  )
}

/* ── 编辑态：单个模型 Card ── */

function ModelCardEdit({
  title,
  prefix,
  form,
  providerOptions,
  getModelOptions,
  saving,
  onSave,
  onCancel,
}: {
  title: string
  prefix: 'sparring' | 'judge'
  form: ReturnType<typeof Form.useForm>[0]
  providerOptions: { value: string; label: string }[]
  getModelOptions: (provider: string | null) => { value: string; label: string }[]
  saving: boolean
  onSave: () => void
  onCancel: () => void
}) {
  return (
    <Card size="small" title={title}>
      <Form.Item name={`${prefix}_provider`} label="厂商">
        <Select options={providerOptions} allowClear placeholder="选择厂商" onChange={() => form.setFieldValue(`${prefix}_model`, null)} />
      </Form.Item>
      <Form.Item noStyle shouldUpdate={(prev, cur) => prev[`${prefix}_provider`] !== cur[`${prefix}_provider`]}>
        {({ getFieldValue }) => (
          <Form.Item name={`${prefix}_model`} label="模型">
            <Select options={getModelOptions(getFieldValue(`${prefix}_provider`))} allowClear placeholder="选择模型" />
          </Form.Item>
        )}
      </Form.Item>
      <Form.Item name={`${prefix}_temperature`} label="Temperature">
        <InputNumber min={0} max={2} step={0.1} style={{ width: '100%' }} />
      </Form.Item>
      <Form.Item name={`${prefix}_max_tokens`} label="Max Tokens">
        <InputNumber min={1} max={16384} style={{ width: '100%' }} />
      </Form.Item>
      <Form.Item name={`${prefix}_system_prompt`} label="System Prompt">
        <Input.TextArea rows={4} />
      </Form.Item>
      <Space>
        <Button type="primary" onClick={onSave} loading={saving}>保存</Button>
        <Button onClick={onCancel}>取消</Button>
      </Space>
    </Card>
  )
}

/* ── 主组件 ── */

export default function ModelConfigTab({ projectId, onDirtyChange }: ModelConfigTabProps) {
  const { data: config, isLoading } = useModelConfig(projectId)
  const { data: modelOptions, isLoading: optionsLoading } = useModelOptions()
  const updateMutation = useUpdateModelConfig(projectId)
  const [form] = Form.useForm()
  const [editingSparring, setEditingSparring] = useState(false)
  const [editingJudge, setEditingJudge] = useState(false)
  const hasAutoEntered = useRef(false)
  const dirtyCards = useRef(new Set<'sparring' | 'judge'>())

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

  const syncForm = useCallback((c: ModelConfig) => {
    form.setFieldsValue(c)
  }, [form])

  const notifyDirty = useCallback((card: 'sparring' | 'judge', dirty: boolean) => {
    if (dirty) dirtyCards.current.add(card)
    else dirtyCards.current.delete(card)
    onDirtyChange?.(dirtyCards.current.size > 0)
  }, [onDirtyChange])

  // 首次无数据自动进入编辑态
  useEffect(() => {
    if (config && !hasAutoEntered.current) {
      hasAutoEntered.current = true
      const needsEdit = !config.sparring_provider || !config.judge_provider
      if (needsEdit) {
        syncForm(config)
        if (!config.sparring_provider) setEditingSparring(true)
        if (!config.judge_provider) setEditingJudge(true)
      }
    }
  }, [config, syncForm])

  const enterEditSparring = useCallback(() => {
    if (config) syncForm(config)
    setEditingSparring(true)
  }, [config, syncForm])

  const enterEditJudge = useCallback(() => {
    if (config) syncForm(config)
    setEditingJudge(true)
  }, [config, syncForm])

  const sparringFields = [
    'sparring_provider', 'sparring_model',
    'sparring_temperature', 'sparring_max_tokens', 'sparring_system_prompt',
  ] as const

  const judgeFields = [
    'judge_provider', 'judge_model',
    'judge_temperature', 'judge_max_tokens', 'judge_system_prompt',
  ] as const

  const saveSparring = async () => {
    try {
      const values = await form.validateFields([...sparringFields])
      const update: ModelConfigUpdate = {
        sparring_provider: values.sparring_provider,
        sparring_model: values.sparring_model,
        sparring_temperature: values.sparring_temperature,
        sparring_max_tokens: values.sparring_max_tokens,
        sparring_system_prompt: values.sparring_system_prompt,
      }
      await updateMutation.mutateAsync(update)
      setEditingSparring(false)
      notifyDirty('sparring', false)
      message.success('保存成功')
    } catch { /* validation */ }
  }

  const saveJudge = async () => {
    try {
      const values = await form.validateFields([...judgeFields])
      const update: ModelConfigUpdate = {
        judge_provider: values.judge_provider,
        judge_model: values.judge_model,
        judge_temperature: values.judge_temperature,
        judge_max_tokens: values.judge_max_tokens,
        judge_system_prompt: values.judge_system_prompt,
      }
      await updateMutation.mutateAsync(update)
      setEditingJudge(false)
      notifyDirty('judge', false)
      message.success('保存成功')
    } catch { /* validation */ }
  }

  if (isLoading) return <Card loading />

  const noProviders = !optionsLoading && providerOptions.length === 0

  return (
    <Form form={form} layout="vertical" onValuesChange={(changed) => {
      const keys = Object.keys(changed)
      if (keys.some(k => k.startsWith('sparring_'))) notifyDirty('sparring', true)
      if (keys.some(k => k.startsWith('judge_'))) notifyDirty('judge', true)
    }}>
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
      <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
        {editingSparring ? (
          <ModelCardEdit
            title="对练模型"
            prefix="sparring"
            form={form}
            providerOptions={providerOptions}
            getModelOptions={getModelOptions}
            saving={updateMutation.isPending}
            onSave={saveSparring}
            onCancel={() => { setEditingSparring(false); notifyDirty('sparring', false) }}
          />
        ) : (
          <ModelCardView
            title="对练模型"
            provider={config?.sparring_provider ?? null}
            model={config?.sparring_model ?? null}
            temperature={config?.sparring_temperature ?? null}
            maxTokens={config?.sparring_max_tokens ?? null}
            systemPrompt={config?.sparring_system_prompt ?? null}
            onEdit={enterEditSparring}
          />
        )}

        {editingJudge ? (
          <ModelCardEdit
            title="裁判模型"
            prefix="judge"
            form={form}
            providerOptions={providerOptions}
            getModelOptions={getModelOptions}
            saving={updateMutation.isPending}
            onSave={saveJudge}
            onCancel={() => { setEditingJudge(false); notifyDirty('judge', false) }}
          />
        ) : (
          <ModelCardView
            title="裁判模型"
            provider={config?.judge_provider ?? null}
            model={config?.judge_model ?? null}
            temperature={config?.judge_temperature ?? null}
            maxTokens={config?.judge_max_tokens ?? null}
            systemPrompt={config?.judge_system_prompt ?? null}
            onEdit={enterEditJudge}
          />
        )}
      </div>
    </Form>
  )
}
