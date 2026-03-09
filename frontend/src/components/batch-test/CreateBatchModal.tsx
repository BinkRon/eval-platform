import { Descriptions, Form, InputNumber, Modal, Select, Tag, message } from 'antd'
import { useAgentVersions } from '../../hooks/useAgentVersions'
import { useCreateBatchTest } from '../../hooks/useBatchTests'
import { useTestCases } from '../../hooks/useTestCases'
import { useJudgeConfig } from '../../hooks/useJudgeConfig'
import { useModelConfig } from '../../hooks/useModelConfig'
import type { BatchTest } from '../../types/batchTest'

interface CreateBatchModalProps {
  projectId: string
  open: boolean
  onClose: () => void
  onCreated?: (batchId: string) => void
}

export default function CreateBatchModal({ projectId, open, onClose, onCreated }: CreateBatchModalProps) {
  const { data: versions } = useAgentVersions(projectId)
  const createMutation = useCreateBatchTest(projectId)
  const { data: testCases } = useTestCases(projectId)
  const { data: judgeConfig } = useJudgeConfig(projectId)
  const { data: modelConfig } = useModelConfig(projectId)

  const [form] = Form.useForm()

  const connectedVersions = (versions || []).filter((v) => v.connection_status === 'success')

  const handleCreate = async () => {
    let values
    try {
      values = await form.validateFields()
    } catch {
      return // 校验失败，表单内联提示已显示
    }
    try {
      const batch: BatchTest = await createMutation.mutateAsync(values)
      message.success('批测已发起')
      onClose()
      onCreated?.(batch.id)
    } catch {
      // 全局拦截器处理 API 错误
    }
  }

  return (
    <Modal title="发起批测" open={open} onOk={handleCreate} onCancel={onClose} confirmLoading={createMutation.isPending}>
      <Form form={form} layout="vertical" initialValues={{ concurrency: 3 }}>
        <Form.Item name="agent_version_id" label="选择 Agent 版本" rules={[{ required: true, message: '请选择版本' }]}>
          <Select
            placeholder="选择要测试的 Agent 版本"
            options={connectedVersions.map((v) => ({ value: v.id, label: v.name }))}
          />
        </Form.Item>
        <Form.Item name="concurrency" label="并发数">
          <InputNumber min={1} max={20} />
        </Form.Item>
      </Form>
      <Descriptions column={1} size="small" style={{ marginTop: 16 }} bordered>
        <Descriptions.Item label="测试用例">{testCases?.length ?? 0} 条（全量）</Descriptions.Item>
        <Descriptions.Item label="裁判配置">
          Checklist {judgeConfig?.checklist_items?.length ?? 0} 条 + Evaluation {judgeConfig?.eval_dimensions?.length ?? 0} 维度
        </Descriptions.Item>
        {(judgeConfig?.checklist_items?.length ?? 0) > 0 && (
          <Descriptions.Item label="Checklist 条目">
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4 }}>
              {judgeConfig!.checklist_items.map((item, i) => (
                <Tag key={i} color={item.level === 'must' ? 'red' : 'orange'}>
                  {item.content}
                </Tag>
              ))}
            </div>
          </Descriptions.Item>
        )}
        {(judgeConfig?.eval_dimensions?.length ?? 0) > 0 && (
          <Descriptions.Item label="评判维度">
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4 }}>
              {judgeConfig!.eval_dimensions.map((dim, i) => (
                <Tag key={i}>{dim.name}</Tag>
              ))}
            </div>
          </Descriptions.Item>
        )}
        <Descriptions.Item label="对练模型">
          {modelConfig?.sparring_provider ?? '-'} / {modelConfig?.sparring_model ?? '-'}
        </Descriptions.Item>
        <Descriptions.Item label="裁判模型">
          {modelConfig?.judge_provider ?? '-'} / {modelConfig?.judge_model ?? '-'}
        </Descriptions.Item>
      </Descriptions>
    </Modal>
  )
}
