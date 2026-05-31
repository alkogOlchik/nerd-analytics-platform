export interface ChatSessionDto {
  id: string
  title: string
  created_at: string
  updated_at: string
  last_message?: string
}

export interface MessageDto {
  id: string
  session_id: string
  role: "user" | "assistant"
  content: string
  created_at: string
}

export interface SendMessageRequest {
  session_id: string
  content: string
}

export interface CreateSessionRequest {
  first_message: string
}

export interface SendMessageResponse {
  user_message: MessageDto
  assistant_message: MessageDto
}

export interface CreateSessionResponse {
  session: ChatSessionDto
  messages: MessageDto[]
}
