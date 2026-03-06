import { useParams, useSearchParams, useNavigate } from 'react-router-dom'
import { Button, Space, Spin, Tabs, Typography } from 'antd'
import { ArrowLeftOutlined } from '@ant-design/icons'
import { useProject } from '../hooks/useProjects'
import AgentVersionTab from '../components/agent-version/AgentVersionTab'
import ExperimentTab from '../components/experiment/ExperimentTab'
import ModelConfigTab from '../components/model-config/ModelConfigTab'
import BatchTestTab from '../components/batch-test/BatchTestTab'

export default function ProjectWorkbench() {
  const { id } = useParams<{ id: string }>()
  const [searchParams, setSearchParams] = useSearchParams()
  const { data: project, isLoading } = useProject(id ?? '')
  const navigate = useNavigate()

  if (!id) return <Typography.Text type="danger">项目 ID 缺失</Typography.Text>

  const activeTab = searchParams.get('tab') || 'agent-versions'

  if (isLoading) return <Spin style={{ display: 'block', margin: '100px auto' }} />
  if (!project) return <Typography.Text type="danger">项目不存在</Typography.Text>

  return (
    <>
      <Space align="center" style={{ marginBottom: 16 }}>
        <Button icon={<ArrowLeftOutlined />} onClick={() => navigate('/projects')}>
          返回项目列表
        </Button>
        <Typography.Title level={3} style={{ margin: 0 }}>{project.name}</Typography.Title>
      </Space>
      {project.description && (
        <Typography.Paragraph type="secondary">{project.description}</Typography.Paragraph>
      )}
      <Tabs
        activeKey={activeTab}
        onChange={(key) => setSearchParams({ tab: key })}
        items={[
          { key: 'agent-versions', label: 'Agent 版本', children: <AgentVersionTab projectId={id} /> },
          { key: 'experiment', label: '实验设计', children: <ExperimentTab projectId={id} /> },
          { key: 'model-config', label: '模型配置', children: <ModelConfigTab projectId={id} /> },
          { key: 'batch-tests', label: '批测中心', children: <BatchTestTab projectId={id} /> },
        ]}
      />
    </>
  )
}
