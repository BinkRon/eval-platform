import { useEffect } from 'react'
import { useParams, useSearchParams } from 'react-router-dom'
import { Card, Spin, Typography } from 'antd'
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

  const targetSection = searchParams.get('section')

  useEffect(() => {
    if (targetSection && SECTION_IDS.includes(targetSection as typeof SECTION_IDS[number])) {
      // Wait for DOM to render
      const timer = setTimeout(() => {
        const el = document.getElementById(targetSection)
        if (el) {
          el.scrollIntoView({ behavior: 'smooth', block: 'start' })
        }
      }, 100)
      return () => clearTimeout(timer)
    }
  }, [targetSection])

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
          <JudgeConfigTab projectId={id} />
        </Card>

        <Card id="model-config" title="模型配置">
          <ModelConfigTab projectId={id} />
        </Card>
      </div>
    </>
  )
}
