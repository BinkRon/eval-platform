import { Button, Card, Collapse, Space, Alert } from 'antd'

export interface GeneratedItem {
  name: string
  summary: string
  fullContent?: string
}

interface GenerateConfirmCardProps {
  title: string
  items: GeneratedItem[]
  impactMessage: string
  loading?: boolean
  onConfirm: () => void
  onModify: () => void
  onCancel: () => void
}

export default function GenerateConfirmCard({
  title,
  items,
  impactMessage,
  loading,
  onConfirm,
  onModify,
  onCancel,
}: GenerateConfirmCardProps) {
  return (
    <Card
      size="small"
      style={{ marginBottom: 12, background: '#fffbe6', border: '1px solid #ffe58f' }}
    >
      <div style={{ fontWeight: 600, marginBottom: 8 }}>
        ✨ 生成完成 — {title}
      </div>

      <div style={{ marginBottom: 8 }}>
        {items.map((item, i) => (
          <div key={i} style={{ marginBottom: 4, fontSize: 13 }}>
            <span style={{ color: '#666' }}>{i + 1}. </span>
            <span style={{ fontWeight: 500 }}>{item.name}</span>
            {item.summary && (
              <span style={{ color: '#888', marginLeft: 4 }}>{item.summary}</span>
            )}
          </div>
        ))}
      </div>

      <Alert
        type="warning"
        message={impactMessage}
        showIcon
        style={{ marginBottom: 8 }}
      />

      {items.some((item) => item.fullContent) && (
        <Collapse
          ghost
          size="small"
          items={[
            {
              key: 'detail',
              label: '展开查看完整配置',
              children: (
                <div style={{ fontSize: 12, whiteSpace: 'pre-wrap', color: '#555' }}>
                  {items
                    .filter((item) => item.fullContent)
                    .map((item, i) => (
                      <div key={i} style={{ marginBottom: 8 }}>
                        <div style={{ fontWeight: 500 }}>{item.name}</div>
                        <div>{item.fullContent}</div>
                      </div>
                    ))}
                </div>
              ),
            },
          ]}
          style={{ marginBottom: 8 }}
        />
      )}

      <div style={{ textAlign: 'right' }}>
        <Space>
          <Button size="small" onClick={onCancel}>
            取消
          </Button>
          <Button size="small" onClick={onModify}>
            修改后再写入
          </Button>
          <Button size="small" type="primary" onClick={onConfirm} loading={loading}>
            确认写入
          </Button>
        </Space>
      </div>
    </Card>
  )
}
