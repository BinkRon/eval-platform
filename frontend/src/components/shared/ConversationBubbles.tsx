import { Avatar } from 'antd'
import { UserOutlined, RobotOutlined } from '@ant-design/icons'

export interface ConversationMessage {
  role: string
  content: string
}

interface ConversationBubblesProps {
  messages: ConversationMessage[]
  maxHeight?: number
}

export default function ConversationBubbles({ messages, maxHeight = 400 }: ConversationBubblesProps) {
  return (
    <div style={{ maxHeight, overflow: 'auto' }}>
      {messages.map((msg, i) => {
        const isUser = msg.role === 'user'
        return (
          <div
            key={`${msg.role}-${i}`}
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
        )
      })}
    </div>
  )
}
