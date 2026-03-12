export interface BuilderChatRequest {
  message: string
  provider: string
  model: string
}

export interface BuilderChatResponse {
  response: string
}
