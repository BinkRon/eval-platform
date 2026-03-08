export interface LatestBatchSummary {
  created_at: string
  agent_version_name: string
  pass_rate: number
  pass_rate_change: number | null
}

export interface Project {
  id: string
  name: string
  description: string | null
  created_at: string
  updated_at: string
  agent_version_count: number
  test_case_count: number
  batch_test_count: number
  latest_batch: LatestBatchSummary | null
}

export interface ConfigReadinessItem {
  ready: boolean
  message: string
}

export interface ConfigReadiness {
  agent_version: ConfigReadinessItem
  test_case: ConfigReadinessItem
  judge_config: ConfigReadinessItem
  model_config_status: ConfigReadinessItem
  all_ready: boolean
}

export interface ProjectCreate {
  name: string
  description?: string
}

export interface ProjectUpdate {
  name?: string
  description?: string
}
