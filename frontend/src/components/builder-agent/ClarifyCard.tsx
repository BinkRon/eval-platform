import { Button, Card, Space } from 'antd'
import { SEMANTIC_COLORS } from '../../theme/themeConfig'

export interface ClarifyOption {
  key: string
  label: string
  description?: string
}

interface ClarifyCardProps {
  question: string
  options: ClarifyOption[]
  onSelect: (key: string) => void
  onSkip: () => void
}

export default function ClarifyCard({
  question,
  options,
  onSelect,
  onSkip,
}: ClarifyCardProps) {
  return (
    <Card
      size="small"
      style={{ marginBottom: 12, background: SEMANTIC_COLORS.clarifyCardBg, border: `1px solid ${SEMANTIC_COLORS.clarifyCardBorder}` }}
    >
      <div style={{ fontWeight: 600, marginBottom: 8 }}>📋 需要确认</div>

      <div style={{ marginBottom: 12, fontSize: 13 }}>{question}</div>

      <div style={{ marginBottom: 8 }}>
        <Space wrap>
          {options.map((opt) => (
            <Button key={opt.key} size="small" onClick={() => onSelect(opt.key)}>
              {opt.label}
              {opt.description && (
                <span style={{ color: SEMANTIC_COLORS.textMuted, marginLeft: 4, fontSize: 12 }}>
                  — {opt.description}
                </span>
              )}
            </Button>
          ))}
        </Space>
      </div>

      <div style={{ textAlign: 'center' }}>
        <Button type="text" size="small" style={{ color: SEMANTIC_COLORS.textMuted }} onClick={onSkip}>
          跳过，按你的理解生成
        </Button>
      </div>
    </Card>
  )
}
