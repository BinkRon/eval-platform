export interface BuilderMessage {
  role: 'user' | 'assistant'
  content: string
  timestamp?: string
}

export interface BuilderConversation {
  id: string
  project_id: string
  messages: BuilderMessage[]
  created_at: string
  updated_at: string
}
