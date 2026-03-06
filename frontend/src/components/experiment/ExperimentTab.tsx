import { Tabs } from 'antd'
import TestCaseTab from '../test-case/TestCaseTab'
import JudgeConfigTab from '../judge-config/JudgeConfigTab'

export default function ExperimentTab({ projectId }: { projectId: string }) {
  return (
    <Tabs
      items={[
        { key: 'test-cases', label: '测试用例集', children: <TestCaseTab projectId={projectId} /> },
        { key: 'judge-config', label: '裁判配置', children: <JudgeConfigTab projectId={projectId} /> },
      ]}
    />
  )
}
