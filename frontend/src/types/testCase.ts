export interface TestCase {
  id: string
  project_id: string
  name: string
  first_message: string
  persona_background: string | null
  persona_behavior: string | null
  max_rounds: number
  sort_order: number
  created_at: string
  updated_at: string
}

export interface TestCaseCreate {
  name: string
  first_message: string
  persona_background?: string
  persona_behavior?: string
  max_rounds?: number
  sort_order?: number
}

export type TestCaseUpdate = Partial<TestCaseCreate>
