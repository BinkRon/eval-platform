import { useParams, useSearchParams } from 'react-router-dom'
import { Spin, Tabs, Typography } from 'antd'
import { useProject } from '../hooks/useProjects'
import AgentVersionTab from '../components/agent-version/AgentVersionTab'
import TestCaseTab from '../components/test-case/TestCaseTab'
import JudgeConfigTab from '../components/judge-config/JudgeConfigTab'
import ModelConfigTab from '../components/model-config/ModelConfigTab'
import BatchTestTab from '../components/batch-test/BatchTestTab'

export default function ProjectWorkbench() {
  const { id } = useParams<{ id: string }>()
  const [searchParams, setSearchParams] = useSearchParams()

  if (!id) return <Typography.Text type="danger">项目 ID 缺失</Typography.Text>

  const { data: project, isLoading } = useProject(id)

  const activeTab = searchParams.get('tab') || 'agent-versions'

  if (isLoading) return <Spin style={{ display: 'block', margin: '100px auto' }} />
  if (!project) return <Typography.Text type="danger">项目不存在</Typography.Text>

  return (
    <>
      <Typography.Title level={3}>{project.name}</Typography.Title>
      {project.description && (
        <Typography.Paragraph type="secondary">{project.description}</Typography.Paragraph>
      )}
      <Tabs
        activeKey={activeTab}
        onChange={(key) => setSearchParams({ tab: key })}
        items={[
          { key: 'agent-versions', label: 'Agent 版本', children: <AgentVersionTab projectId={id} /> },
          { key: 'test-cases', label: '测试用例', children: <TestCaseTab projectId={id} /> },
          { key: 'judge-config', label: '裁判配置', children: <JudgeConfigTab projectId={id} /> },
          { key: 'model-config', label: '模型配置', children: <ModelConfigTab projectId={id} /> },
          { key: 'batch-tests', label: '批测中心', children: <BatchTestTab projectId={id} /> },
        ]}
      />
    </>
  )
}
