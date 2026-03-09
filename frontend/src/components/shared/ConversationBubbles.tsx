import { useEffect, useRef } from 'react'
import { Avatar } from 'antd'
import { UserOutlined, RobotOutlined } from '@ant-design/icons'

export interface ConversationMessage {
  role: string
  content: string
}

interface ConversationBubblesProps {
  messages: ConversationMessage[]
  /** CSS height value, e.g. "calc(100vh - 280px)". Falls back to maxHeight for backward compat. */
  height?: string
  /** @deprecated Use height instead */
  maxHeight?: number
}

export default function ConversationBubbles({ messages, height, maxHeight = 400 }: ConversationBubblesProps) {
  const containerRef = useRef<HTMLDivElement>(null)
  const prevCountRef = useRef(0)

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    if (messages.length > prevCountRef.current && containerRef.current) {
      containerRef.current.scrollTop = containerRef.current.scrollHeight
    }
    prevCountRef.current = messages.length
  }, [messages.length])

  const containerStyle: React.CSSProperties = height
    ? { height, overflow: 'auto' }
    : { maxHeight, overflow: 'auto' }

  // Compute round number for each message (one round = user + assistant)
  let roundCounter = 0
  const roundNumbers = messages.map((msg) => {
    if (msg.role === 'user') roundCounter++
    return roundCounter
  })

  return (
    <div ref={containerRef} style={containerStyle}>
      {messages.map((msg, i) => {
        const isUser = msg.role === 'user'
        const showRoundLabel = isUser
        return (
          <div key={`${msg.role}-${i}`}>
            {showRoundLabel && (
              <div style={{
                textAlign: 'center',
                margin: i === 0 ? '0 0 8px' : '16px 0 8px',
                fontSize: 12,
                color: '#999',
              }}>
                R{roundNumbers[i]}
              </div>
            )}
            <div
              style={{
                marginBottom: 12,
                display: 'flex',
                flexDirection: isUser ? 'row' : 'row-reverse',
                alignItems: 'flex-start',
                gap: 8,
              }}
            >
              <Avatar
                size="small"
                icon={isUser ? <UserOutlined /> : <RobotOutlined />}
                style={{ backgroundColor: isUser ? '#1677ff' : '#52c41a', flexShrink: 0 }}
              />
              <div style={{
                maxWidth: '70%',
                padding: '8px 12px',
                borderRadius: 8,
                background: isUser ? '#e6f4ff' : '#f6ffed',
                textAlign: 'left',
                whiteSpace: 'pre-wrap',
                wordBreak: 'break-word',
              }}>
                {msg.content}
              </div>
            </div>
          </div>
        )
      })}
    </div>
  )
}
