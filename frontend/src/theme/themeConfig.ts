import type { ThemeConfig } from 'antd'

export const warmTheme: ThemeConfig = {
  token: {
    colorPrimary: '#2d7a4e',
    colorSuccess: '#2d7a4e',
    colorWarning: '#8b7a2e',
    colorError: '#c2452d',
    colorInfo: '#2d6b96',
    colorBgBase: '#f3f1ec',
    colorBgContainer: '#ffffff',
    colorBgLayout: '#f3f1ec',
    colorTextBase: '#1c1c1a',
    colorSuccessBg: '#e8f5ee',
    colorSuccessBorder: '#b7dfca',
    colorErrorBg: '#fce8e4',
    colorErrorBorder: '#f0bdb3',
    colorBorder: '#e5e3dc',
    colorBorderSecondary: '#eeedea',
    borderRadius: 10,
    fontFamily: "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif",
  },
  components: {
    Layout: {
      siderBg: '#faf9f6',
      bodyBg: '#f3f1ec',
    },
    Menu: {
      itemSelectedBg: '#e3f0e8',
      itemSelectedColor: '#22633f',
      itemHoverBg: '#eeedea',
    },
    Table: {
      headerBg: '#f5f4f1',
      rowHoverBg: '#eef5f0',
    },
    Tag: {
      borderRadiusSM: 20,
    },
    Button: {
      primaryShadow: 'none',
      defaultShadow: 'none',
      dangerShadow: 'none',
    },
    Progress: {
      defaultColor: '#2d7a4e',
    },
    Breadcrumb: {
      linkColor: '#5e5e58',
      separatorColor: '#9b9b90',
    },
  },
}

export const SEMANTIC_COLORS = {
  // Conversation bubbles
  userAvatarBg: '#2d7a4e',
  botAvatarBg: '#ddddd4',
  userBubbleBg: '#e3f0e8',
  botBubbleBg: '#f5f4f1',

  // Builder cards
  generateCardBg: '#f9f3d5',
  generateCardBorder: '#e8dfa0',
  overwriteCardBg: '#faf5ec',
  overwriteCardBorder: '#e5d5b0',
  clarifyCardBg: '#e4f0f8',
  clarifyCardBorder: '#a8cfe0',

  // Pass rate
  passRateUp: '#22633f',
  passRateDown: '#c2452d',

  // Brand / primary
  brandPrimary: '#2d7a4e',
  colorWarning: '#8b7a2e',

  // Border & background
  borderDefault: '#e5e3dc',
  codeBg: '#f5f4f1',

  // Text
  textSecondary: '#5e5e58',
  textMuted: '#9b9b90',
} as const
