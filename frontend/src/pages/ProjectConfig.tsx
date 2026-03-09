import { useCallback, useEffect, useState } from 'react'
import { useParams, useSearchParams, useBlocker } from 'react-router-dom'
import { Card, Modal, Spin, Typography } from 'antd'
import { useProject } from '../hooks/useProjects'
import BreadcrumbNav from '../components/shared/BreadcrumbNav'
import AgentVersionTab from '../components/agent-version/AgentVersionTab'
import TestCaseTab from '../components/test-case/TestCaseTab'
import JudgeConfigTab from '../components/judge-config/JudgeConfigTab'
import ModelConfigTab from '../components/model-config/ModelConfigTab'

const SECTION_IDS = ['agent-versions', 'test-cases', 'judge-config', 'model-config'] as const

export default function ProjectConfig() {
  const { id } = useParams<{ id: string }>()
  const [searchParams] = useSearchParams()
  const { data: project, isLoading } = useProject(id ?? '')

  // Track dirty state from judge config and model config
  const [judgeDirty, setJudgeDirty] = useState(false)
  const [modelDirty, setModelDirty] = useState(false)
  const hasDirty = judgeDirty || modelDirty

  // Block navigation when there are unsaved changes
  const blocker = useBlocker(hasDirty)

  useEffect(() => {
    if (blocker.state === 'blocked') {
      Modal.confirm({
        title: '有未保存的更改',
        content: '裁判配置或模型配置有未保存的更改，确定离开？',
        okText: '离开',
        okType: 'danger',
        cancelText: '继续编辑',
        onOk: () => blocker.proceed(),
        onCancel: () => blocker.reset(),
      })
    }
  }, [blocker])

  // Warn on browser close/refresh
  useEffect(() => {
    if (!hasDirty) return
    const handler = (e: BeforeUnloadEvent) => {
      e.preventDefault()
    }
    window.addEventListener('beforeunload', handler)
    return () => window.removeEventListener('beforeunload', handler)
  }, [hasDirty])

  const targetSection = searchParams.get('section')

  useEffect(() => {
    if (targetSection && SECTION_IDS.includes(targetSection as typeof SECTION_IDS[number])) {
      const timer = setTimeout(() => {
        const el = document.getElementById(targetSection)
        if (el) {
          el.scrollIntoView({ behavior: 'smooth', block: 'start' })
        }
      }, 100)
      return () => clearTimeout(timer)
    }
  }, [targetSection])

  const handleJudgeDirty = useCallback((dirty: boolean) => setJudgeDirty(dirty), [])
  const handleModelDirty = useCallback((dirty: boolean) => setModelDirty(dirty), [])

  if (!id) return <Typography.Text type="danger">项目 ID 缺失</Typography.Text>
  if (isLoading) return <Spin style={{ display: 'block', margin: '100px auto' }} />
  if (!project) return <Typography.Text type="danger">项目不存在</Typography.Text>

  return (
    <>
      <BreadcrumbNav items={[
        { title: '项目列表', path: '/projects' },
        { title: project.name, path: `/projects/${id}` },
        { title: '项目配置' },
      ]} />
      <Typography.Title level={3} style={{ marginBottom: 8, marginTop: 0 }}>{project.name} · 项目配置</Typography.Title>

      <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
        <Card id="agent-versions" title="Agent 版本">
          <AgentVersionTab projectId={id} />
        </Card>

        <Card id="test-cases" title="测试用例集">
          <TestCaseTab projectId={id} />
        </Card>

        <Card id="judge-config" title="裁判配置">
          <JudgeConfigTab projectId={id} onDirtyChange={handleJudgeDirty} />
        </Card>

        <Card id="model-config" title="模型配置">
          <ModelConfigTab projectId={id} onDirtyChange={handleModelDirty} />
        </Card>
      </div>
    </>
  )
}
