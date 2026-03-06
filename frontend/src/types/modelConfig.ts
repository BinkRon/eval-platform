export interface ModelConfig {
  id: string
  project_id: string
  sparring_provider: string | null
  sparring_model: string | null
  sparring_temperature: number | null
  sparring_max_tokens: number | null
  sparring_system_prompt: string | null
  judge_provider: string | null
  judge_model: string | null
  judge_temperature: number | null
  judge_max_tokens: number | null
  judge_system_prompt: string | null
}

export type ModelConfigUpdate = Partial<Omit<ModelConfig, 'id' | 'project_id'>>

export interface ModelOption {
  provider: string
  model: string
}
