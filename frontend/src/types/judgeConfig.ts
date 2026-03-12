export interface ChecklistItem {
  id?: string
  content: string
  level: string
  sort_order: number
}

export interface EvalDimension {
  id?: string
  name: string
  judge_prompt_segment: string
  sort_order: number
}

export interface JudgeConfig {
  id: string
  project_id: string
  pass_threshold: number
  checklist_items: ChecklistItem[]
  eval_dimensions: EvalDimension[]
}

export interface JudgeConfigUpdate {
  pass_threshold: number
  checklist_items: ChecklistItem[]
  eval_dimensions: EvalDimension[]
}
