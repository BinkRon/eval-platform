import { useState } from 'react'
import { Button, Card, Radio, Space } from 'antd'
import { SEMANTIC_COLORS } from '../../theme/themeConfig'

interface CountItem {
  label: string
  count: number
}

interface OverwriteConfirmCardProps {
  title: string
  existingCounts: CountItem[]
  newCounts: CountItem[]
  loading?: boolean
  onConfirm: (mode: 'append' | 'replace') => void
  onCancel: () => void
}

export default function OverwriteConfirmCard({
  title,
  existingCounts,
  newCounts,
  loading,
  onConfirm,
  onCancel,
}: OverwriteConfirmCardProps) {
  const [mode, setMode] = useState<'append' | 'replace'>('append')

  return (
    <Card
      size="small"
      style={{ marginBottom: 12, background: SEMANTIC_COLORS.overwriteCardBg, border: `1px solid ${SEMANTIC_COLORS.overwriteCardBorder}` }}
    >
      <div style={{ fontWeight: 600, marginBottom: 8 }}>
        ⚠️ 覆盖确认 — {title}
      </div>

      <div style={{ marginBottom: 8, fontSize: 13 }}>
        <div style={{ color: SEMANTIC_COLORS.textSecondary, marginBottom: 4 }}>目标区块已有配置：</div>
        {existingCounts.map((item, i) => (
          <div key={i} style={{ paddingLeft: 12 }}>
            · {item.label}: {item.count} 条
          </div>
        ))}
      </div>

      <div style={{ marginBottom: 8, fontSize: 13 }}>
        <div style={{ color: SEMANTIC_COLORS.textSecondary, marginBottom: 4 }}>本次生成：</div>
        {newCounts.map((item, i) => (
          <div key={i} style={{ paddingLeft: 12 }}>
            · {item.label}: {item.count} 条
          </div>
        ))}
      </div>

      <Radio.Group
        value={mode}
        onChange={(e) => setMode(e.target.value)}
        style={{ marginBottom: 12 }}
      >
        <Radio value="append">追加到现有配置</Radio>
        <Radio value="replace">替换全部现有配置</Radio>
      </Radio.Group>

      <div style={{ textAlign: 'right' }}>
        <Space>
          <Button size="small" onClick={onCancel}>
            取消
          </Button>
          <Button size="small" type="primary" onClick={() => onConfirm(mode)} loading={loading}>
            确认执行
          </Button>
        </Space>
      </div>
    </Card>
  )
}
