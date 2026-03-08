import { useParams, useNavigate } from 'react-router-dom'
import { Button, Spin, Typography } from 'antd'
import { ArrowLeftOutlined } from '@ant-design/icons'

export default function DialogTheater() {
  const { id: projectId, bid: batchId, rid } = useParams<{ id: string; bid: string; rid: string }>()
  const navigate = useNavigate()

  if (!projectId || !batchId || !rid) return <Typography.Text type="danger">路由参数缺失</Typography.Text>

  return (
    <>
      <Button
        icon={<ArrowLeftOutlined />}
        onClick={() => navigate(`/projects/${projectId}/batch-tests/${batchId}`)}
        style={{ marginBottom: 16 }}
      >
        返回用例概览
      </Button>
      <Typography.Title level={4}>对话剧场</Typography.Title>
      <Typography.Text type="secondary">Phase 5 实现中…</Typography.Text>
    </>
  )
}
