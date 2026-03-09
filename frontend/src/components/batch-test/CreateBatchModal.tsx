import { useEffect, useMemo, useRef } from 'react'
import { Descriptions, Divider, Form, InputNumber, Modal, Select, message } from 'antd'
import { useAgentVersions } from '../../hooks/useAgentVersions'
import { useCreateBatchTest } from '../../hooks/useBatchTests'
import { useTestCases } from '../../hooks/useTestCases'
import { useJudgeConfig } from '../../hooks/useJudgeConfig'
import { useModelConfig } from '../../hooks/useModelConfig'
import type { BatchTest, BatchTestCreate } from '../../types/batchTest'

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
  const defaultsSetRef = useRef(false)

  const connectedVersions = (versions || []).filter((v) => v.connection_status === 'success')

  const allTestCaseIds = useMemo(() => (testCases || []).map((tc) => tc.id), [testCases])
  const allChecklistItemIds = useMemo(
    () => (judgeConfig?.checklist_items || []).map((ci) => ci.id).filter(Boolean) as string[],
    [judgeConfig],
  )
  const allEvalDimensionIds = useMemo(
    () => (judgeConfig?.eval_dimensions || []).map((ed) => ed.id).filter(Boolean) as string[],
    [judgeConfig],
  )

  // Set multi-select defaults when modal opens and data is ready
  useEffect(() => {
    if (!open) {
      defaultsSetRef.current = false
      return
    }
    if (!defaultsSetRef.current && testCases && judgeConfig) {
      defaultsSetRef.current = true
      form.setFieldsValue({
        test_case_ids: allTestCaseIds,
        checklist_item_ids: allChecklistItemIds,
        eval_dimension_ids: allEvalDimensionIds,
        pass_threshold: judgeConfig.pass_threshold ?? 2.0,
      })
    }
  }, [open, testCases, judgeConfig, allTestCaseIds, allChecklistItemIds, allEvalDimensionIds, form])

  const selectedTestCaseIds: string[] = Form.useWatch('test_case_ids', form) || []
  const selectedChecklistIds: string[] = Form.useWatch('checklist_item_ids', form) || []
  const selectedDimensionIds: string[] = Form.useWatch('eval_dimension_ids', form) || []

  const handleCreate = async () => {
    let values: Record<string, unknown>
    try {
      values = await form.validateFields()
    } catch {
      return
    }
    try {
      const payload: BatchTestCreate = {
        agent_version_id: values.agent_version_id as string,
        concurrency: values.concurrency as number,
      }
      // Only send IDs when partially selected (PRD §2.4)
      const tcIds = values.test_case_ids as string[] | undefined
      if (tcIds && tcIds.length < allTestCaseIds.length) {
        payload.test_case_ids = tcIds
      }
      const ciIds = values.checklist_item_ids as string[] | undefined
      if (ciIds && ciIds.length < allChecklistItemIds.length) {
        payload.checklist_item_ids = ciIds
      }
      const edIds = values.eval_dimension_ids as string[] | undefined
      if (edIds && edIds.length < allEvalDimensionIds.length) {
        payload.eval_dimension_ids = edIds
      }
      if (values.pass_threshold != null) {
        payload.pass_threshold = values.pass_threshold as number
      }

      const batch: BatchTest = await createMutation.mutateAsync(payload)
      message.success('批测已发起')
      form.resetFields()
      onClose()
      onCreated?.(batch.id)
    } catch (err: unknown) {
      // 全局拦截器处理 API 错误，此处兜底
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail
      if (detail) message.error(detail)
    }
  }

  const handleCancel = () => {
    form.resetFields()
    onClose()
  }

  return (
    <Modal title="发起批测" open={open} onOk={handleCreate} onCancel={handleCancel} confirmLoading={createMutation.isPending} width={560}>
      <Form form={form} layout="vertical" initialValues={{ concurrency: 3 }}>
        <Form.Item name="agent_version_id" label="选择 Agent 版本" rules={[{ required: true, message: '请选择版本' }]}>
          <Select
            placeholder="选择要测试的 Agent 版本"
            options={connectedVersions.map((v) => ({ value: v.id, label: v.name }))}
          />
        </Form.Item>
        <Form.Item name="concurrency" label="并发数">
          <InputNumber min={1} max={20} style={{ width: '100%' }} />
        </Form.Item>

        <Form.Item
          name="test_case_ids"
          label={`测试用例（${selectedTestCaseIds.length}/${allTestCaseIds.length}）`}
        >
          <Select
            mode="multiple"
            maxTagCount="responsive"
            placeholder="选择测试用例"
            options={(testCases || []).map((tc) => ({ value: tc.id, label: tc.name }))}
          />
        </Form.Item>

        <Form.Item
          name="checklist_item_ids"
          label={`Checklist 检查项（${selectedChecklistIds.length}/${allChecklistItemIds.length}）`}
        >
          <Select
            mode="multiple"
            maxTagCount="responsive"
            placeholder="选择检查项"
            options={(judgeConfig?.checklist_items || [])
              .filter((ci) => ci.id)
              .map((ci) => ({
                value: ci.id!,
                label: `${ci.content}（${ci.level === 'must' ? '必须' : '应该'}）`,
              }))}
          />
        </Form.Item>

        <Form.Item
          name="eval_dimension_ids"
          label={`评判维度（${selectedDimensionIds.length}/${allEvalDimensionIds.length}）`}
        >
          <Select
            mode="multiple"
            maxTagCount="responsive"
            placeholder="选择评判维度"
            options={(judgeConfig?.eval_dimensions || [])
              .filter((ed) => ed.id)
              .map((ed) => ({ value: ed.id!, label: ed.name }))}
          />
        </Form.Item>

        <Form.Item name="pass_threshold" label="通过阈值">
          <InputNumber min={1} max={3} step={0.1} style={{ width: '100%' }} />
        </Form.Item>
      </Form>

      <Divider style={{ margin: '12px 0' }}>模型配置（只读）</Divider>
      <Descriptions column={1} size="small" bordered>
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
