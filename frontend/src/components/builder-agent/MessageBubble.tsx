import { Avatar } from 'antd'
import { UserOutlined, RobotOutlined } from '@ant-design/icons'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import rehypeSanitize from 'rehype-sanitize'
import { SEMANTIC_COLORS } from '../../theme/themeConfig'

interface MessageBubbleProps {
  role: 'user' | 'assistant'
  content: string
}

export default function MessageBubble({ role, content }: MessageBubbleProps) {
  const isUser = role === 'user'

  return (
    <div
      style={{
        marginBottom: 12,
        display: 'flex',
        flexDirection: isUser ? 'row-reverse' : 'row',
        alignItems: 'flex-start',
        gap: 8,
      }}
    >
      <Avatar
        size="small"
        icon={isUser ? <UserOutlined /> : <RobotOutlined />}
        style={{ backgroundColor: isUser ? SEMANTIC_COLORS.userAvatarBg : SEMANTIC_COLORS.botAvatarBg, flexShrink: 0 }}
      />
      <div
        style={{
          maxWidth: '75%',
          padding: '8px 12px',
          borderRadius: 8,
          background: isUser ? SEMANTIC_COLORS.userBubbleBg : SEMANTIC_COLORS.botBubbleBg,
          textAlign: 'left',
          wordBreak: 'break-word',
        }}
      >
        {isUser ? (
          <div style={{ whiteSpace: 'pre-wrap' }}>{content}</div>
        ) : (
          <div className="builder-markdown">
            <ReactMarkdown remarkPlugins={[remarkGfm]} rehypePlugins={[rehypeSanitize]}>{content}</ReactMarkdown>
          </div>
        )}
      </div>
    </div>
  )
}
