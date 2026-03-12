export interface TestCase {
  id: string
  project_id: string
  name: string
  sparring_prompt: string
  first_message: string | null
  max_rounds: number
  sort_order: number
  created_at: string
  updated_at: string
  last_result: string | null
}

export interface TestCaseCreate {
  name: string
  sparring_prompt: string
  first_message?: string | null
  max_rounds?: number
  sort_order?: number
}

export type TestCaseUpdate = Partial<TestCaseCreate>
