export interface BatchTest {
  id: string
  project_id: string
  agent_version_id: string | null
  agent_version_name: string | null
  status: string
  concurrency: number
  total_cases: number
  passed_cases: number
  completed_cases: number
  created_at: string
  completed_at: string | null
}

export interface BatchTestCreate {
  agent_version_id: string
  concurrency?: number
}

export interface TestResult {
  id: string
  batch_test_id: string
  test_case_id: string | null
  test_case_name: string | null
  status: string
  conversation: { role: string; content: string }[] | null
  termination_reason: string | null
  actual_rounds: number | null
  checklist_results: { content: string; level: string; passed: boolean; reason: string }[] | null
  eval_scores: { dimension: string; score: number; reason: string }[] | null
  judge_summary: string | null
  passed: boolean | null
  error_message: string | null
}

export interface BatchTestDetail extends BatchTest {
  test_results: TestResult[]
}
