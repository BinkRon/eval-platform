export interface ChecklistItem {
  id?: string
  content: string
  level: string
  sort_order: number
}

export interface EvalDimension {
  id?: string
  name: string
  description?: string
  level_3_desc?: string
  level_2_desc?: string
  level_1_desc?: string
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
