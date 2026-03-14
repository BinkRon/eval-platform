import { useEffect, useRef, useState } from 'react'
import { Button, Input, Modal, Select, Space, Spin, message } from 'antd'
import { MinusOutlined, SendOutlined, DeleteOutlined, ExclamationCircleOutlined } from '@ant-design/icons'
import { useQueryClient } from '@tanstack/react-query'
import { useBuilderConversation, useClearConversation } from '../../hooks/useBuilderConversation'
import { useSendBuilderMessage, useApplyConfig } from '../../hooks/useBuilderAgent'
import { useModelOptions } from '../../hooks/useModelConfig'
import MessageBubble from './MessageBubble'
import GenerateConfirmCard from './GenerateConfirmCard'
import OverwriteConfirmCard from './OverwriteConfirmCard'
import ProjectFileManager from './ProjectFileManager'
import type { BuilderMessage } from '../../types/builderConversation'
import type { GenerateConfirmCardData } from '../../types/builderAgent'
import { SEMANTIC_COLORS } from '../../theme/themeConfig'

interface ChatPanelProps {
  projectId: string
  open: boolean
  onClose: () => void
}

export default function ChatPanel({ projectId, open, onClose }: ChatPanelProps) {
  const { data: conversation, isLoading: conversationLoading } =
    useBuilderConversation(projectId)
  const { data: modelOptions = [] } = useModelOptions()
  const sendMutation = useSendBuilderMessage(projectId)
  const clearMutation = useClearConversation(projectId)
  const applyMutation = useApplyConfig(projectId)
  const queryClient = useQueryClient()

  const [inputValue, setInputValue] = useState('')
  const [selectedModel, setSelectedModel] = useState<string>('')
  const [pendingCard, setPendingCard] = useState<GenerateConfirmCardData | null>(null)
  const [showOverwrite, setShowOverwrite] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  // Set default model when options load
  useEffect(() => {
    if (modelOptions.length > 0 && !selectedModel) {
      setSelectedModel(`${modelOptions[0].provider}::${modelOptions[0].model}`)
    }
  }, [modelOptions, selectedModel])

  // Auto-scroll to bottom on new messages
  const messages = conversation?.messages ?? []
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages.length])

  const parseModel = (value: string) => {
    const [provider, model] = value.split('::')
    return { provider, model }
  }

  const handleSend = () => {
    const text = inputValue.trim()
    if (!text || sendMutation.isPending || !selectedModel) return

    const { provider, model } = parseModel(selectedModel)

    // Snapshot current length for safe rollback
    const snapshotLen = conversation?.messages.length ?? 0

    // Optimistic update: add user message immediately
    const userMsg: BuilderMessage = { role: 'user', content: text }
    queryClient.setQueryData(
      ['builder-conversation', projectId],
      (old: typeof conversation) =>
        old ? { ...old, messages: [...old.messages, userMsg] } : old
    )

    setInputValue('')

    sendMutation.mutate(
      { message: text, provider, model },
      {
        onSuccess: (data) => {
          // Add assistant response to cache
          const assistantMsg: BuilderMessage = {
            role: 'assistant',
            content: data.response,
          }
          queryClient.setQueryData(
            ['builder-conversation', projectId],
            (old: typeof conversation) =>
              old ? { ...old, messages: [...old.messages, assistantMsg] } : old
          )
          // Show confirm card if config was generated
          if (data.card_type === 'generate_confirm' && data.card_data) {
            setPendingCard(data.card_data)
            setShowOverwrite(false)
          }
        },
        onError: () => {
          // Rollback to snapshot length
          queryClient.setQueryData(
            ['builder-conversation', projectId],
            (old: typeof conversation) =>
              old ? { ...old, messages: old.messages.slice(0, snapshotLen) } : old
          )
        },
      }
    )
  }

  const handleConfirmWrite = (mode: 'append' | 'replace' = 'append') => {
    if (!pendingCard) return
    applyMutation.mutate(
      {
        config_type: pendingCard.config_type,
        config_payload: pendingCard.config_payload,
        mode,
      },
      {
        onSuccess: () => {
          message.success('配置已写入')
          setPendingCard(null)
          setShowOverwrite(false)
        },
        onError: () => {
          message.error('写入失败，请重试')
        },
      }
    )
  }

  const handleModify = () => {
    setPendingCard(null)
    setShowOverwrite(false)
    setInputValue('请帮我修改上面生成的配置，')
  }

  const handleCancelCard = () => {
    setPendingCard(null)
    setShowOverwrite(false)
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  if (!open) return null

  const modelSelectOptions = modelOptions.map((o) => ({
    label: `${o.provider} / ${o.model}`,
    value: `${o.provider}::${o.model}`,
  }))

  return (
    <div
      style={{
        position: 'fixed',
        right: 24,
        bottom: 24,
        width: 420,
        height: 'min(600px, calc(100vh - 120px))',
        borderRadius: 12,
        boxShadow: '0 6px 16px rgba(0,0,0,0.12)',
        background: '#fff',
        display: 'flex',
        flexDirection: 'column',
        zIndex: 1000,
        overflow: 'hidden',
      }}
    >
      {/* Header */}
      <div
        style={{
          padding: '12px 16px',
          borderBottom: `1px solid ${SEMANTIC_COLORS.borderDefault}`,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          flexShrink: 0,
        }}
      >
        <span style={{ fontWeight: 600, fontSize: 14 }}>构建助手</span>
        <Space size={4}>
          <ProjectFileManager projectId={projectId} />
          <Select
            size="small"
            style={{ width: 180 }}
            value={selectedModel || undefined}
            onChange={setSelectedModel}
            options={modelSelectOptions}
            placeholder="选择模型"
          />
          <Button
            type="text"
            size="small"
            icon={<DeleteOutlined />}
            onClick={() => {
              Modal.confirm({
                title: '清空对话',
                icon: <ExclamationCircleOutlined />,
                content: '确认清空所有对话记录？此操作不可恢复。',
                okText: '清空',
                cancelText: '取消',
                onOk: () => clearMutation.mutateAsync(),
              })
            }}
            title="清空对话"
          />
          <Button
            type="text"
            size="small"
            icon={<MinusOutlined />}
            onClick={onClose}
            title="收起"
          />
        </Space>
      </div>

      {/* Messages */}
      <div style={{ flex: 1, overflowY: 'auto', padding: 16 }}>
        {conversationLoading ? (
          <div style={{ textAlign: 'center', padding: 40 }}>
            <Spin />
          </div>
        ) : messages.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '40px 20px', color: SEMANTIC_COLORS.textMuted }}>
            <div style={{ fontSize: 32, marginBottom: 12 }}>🤖</div>
            <div>你好！我是构建助手。</div>
            <div style={{ fontSize: 13, marginTop: 4 }}>
              描述你的评测场景，我可以帮你生成测试用例和裁判配置。
            </div>
          </div>
        ) : (
          messages.map((msg, i) => (
            <MessageBubble key={i} role={msg.role} content={msg.content} />
          ))
        )}
        {sendMutation.isPending && (
          <div style={{ textAlign: 'center', padding: '8px 0' }}>
            <Spin size="small" />
            <span style={{ marginLeft: 8, fontSize: 12, color: SEMANTIC_COLORS.textMuted }}>思考中...</span>
          </div>
        )}
        {/* Confirm card */}
        {pendingCard && !showOverwrite && (
          <GenerateConfirmCard
            title={pendingCard.title}
            items={pendingCard.items}
            impactMessage={pendingCard.impact_message}
            loading={applyMutation.isPending}
            onConfirm={() => {
              // If existing data, show overwrite card; otherwise write directly
              if (pendingCard.existing_count > 0) {
                setShowOverwrite(true)
              } else {
                handleConfirmWrite('append')
              }
            }}
            onModify={handleModify}
            onCancel={handleCancelCard}
          />
        )}
        {pendingCard && showOverwrite && (
          <OverwriteConfirmCard
            title={pendingCard.title}
            loading={applyMutation.isPending}
            existingCounts={
              pendingCard.config_type === 'test_cases'
                ? [{ label: '测试用例', count: pendingCard.existing_count }]
                : [
                    { label: 'Checklist', count: pendingCard.existing_checklist_count ?? 0 },
                    { label: 'Evaluation 维度', count: pendingCard.existing_dimension_count ?? 0 },
                  ]
            }
            newCounts={
              pendingCard.config_type === 'test_cases'
                ? [{ label: '测试用例', count: pendingCard.items.length }]
                : [
                    { label: 'Checklist', count: pendingCard.new_checklist_count ?? 0 },
                    { label: 'Evaluation 维度', count: pendingCard.new_dimension_count ?? 0 },
                  ]
            }
            onConfirm={handleConfirmWrite}
            onCancel={handleCancelCard}
          />
        )}
        {applyMutation.isPending && (
          <div style={{ textAlign: 'center', padding: '8px 0' }}>
            <Spin size="small" />
            <span style={{ marginLeft: 8, fontSize: 12, color: SEMANTIC_COLORS.textMuted }}>写入中...</span>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div
        style={{
          padding: '12px 16px',
          borderTop: `1px solid ${SEMANTIC_COLORS.borderDefault}`,
          flexShrink: 0,
        }}
      >
        <div style={{ display: 'flex', gap: 8, alignItems: 'flex-end' }}>
          <Input.TextArea
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="输入消息..."
            autoSize={{ minRows: 1, maxRows: 4 }}
            disabled={sendMutation.isPending}
            style={{ flex: 1 }}
          />
          <Button
            type="primary"
            icon={<SendOutlined />}
            onClick={handleSend}
            loading={sendMutation.isPending}
            disabled={!inputValue.trim() || !selectedModel}
          />
        </div>
      </div>
    </div>
  )
}
