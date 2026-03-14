import { useEffect, useState } from 'react'
import { Button } from 'antd'
import { RobotOutlined } from '@ant-design/icons'
import ChatPanel from './ChatPanel'

interface FloatingButtonProps {
  projectId: string
}

export default function FloatingButton({ projectId }: FloatingButtonProps) {
  const [panelOpen, setPanelOpen] = useState(false)

  // Close panel when switching projects
  useEffect(() => {
    setPanelOpen(false)
  }, [projectId])

  return (
    <>
      {!panelOpen && (
        <Button
          shape="circle"
          size="large"
          type="primary"
          icon={<RobotOutlined />}
          onClick={() => setPanelOpen(true)}
          style={{
            position: 'fixed',
            right: 24,
            bottom: 24,
            zIndex: 999,
            width: 48,
            height: 48,
            boxShadow: '0 4px 12px rgba(45,122,78,0.3)',
          }}
        />
      )}
      <ChatPanel
        projectId={projectId}
        open={panelOpen}
        onClose={() => setPanelOpen(false)}
      />
    </>
  )
}
