export interface BuilderChatRequest {
  message: string
  provider: string
  model: string
}

export interface BuilderChatResponse {
  response: string
  card_type: 'generate_confirm' | null
  card_data: GenerateConfirmCardData | null
}

export interface GeneratedConfigItem {
  name: string
  summary: string
  fullContent?: string
}

export interface GenerateConfirmCardData {
  config_type: 'test_cases' | 'judge_config'
  title: string
  items: GeneratedConfigItem[]
  impact_message: string
  existing_count: number
  existing_checklist_count?: number
  existing_dimension_count?: number
  new_checklist_count?: number
  new_dimension_count?: number
  config_payload: Record<string, unknown>
}

export interface ApplyConfigRequest {
  config_type: 'test_cases' | 'judge_config'
  config_payload: Record<string, unknown>
  mode: 'append' | 'replace'
}

export interface ApplyConfigResponse {
  success: boolean
  summary: Record<string, unknown>
}
