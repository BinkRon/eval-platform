export interface AgentVersion {
  id: string
  project_id: string
  name: string
  description: string | null
  endpoint: string | null
  method: string
  auth_type: string | null
  auth_token_set: boolean
  request_template: string | null
  response_path: string | null
  has_end_signal: boolean
  end_signal_path: string | null
  end_signal_value: string | null
  connection_status: string
  created_at: string
  updated_at: string
}

export interface AgentVersionCreate {
  name: string
  description?: string
  endpoint?: string
  method?: string
  auth_type?: string
  auth_token?: string
  request_template?: string
  response_path?: string
  has_end_signal?: boolean
  end_signal_path?: string
  end_signal_value?: string
}

export type AgentVersionUpdate = Partial<AgentVersionCreate>
