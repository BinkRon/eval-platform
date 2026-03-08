import { Tag } from 'antd'

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
      {messages.map((msg, i) => (
        <div key={`${msg.role}-${i}`} style={{ marginBottom: 12, textAlign: msg.role === 'user' ? 'left' : 'right' }}>
          <Tag color={msg.role === 'user' ? 'blue' : 'green'}>
            {msg.role === 'user' ? '对练' : 'Agent'}
          </Tag>
          <div style={{
            display: 'inline-block', maxWidth: '70%',
            padding: '8px 12px', borderRadius: 8,
            background: msg.role === 'user' ? '#e6f4ff' : '#f6ffed',
            textAlign: 'left',
          }}>
            {msg.content}
          </div>
        </div>
      ))}
    </div>
  )
}
