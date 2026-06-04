export interface ChatSessionDto {
  id: string
  title: string
  created_at: string
  updated_at: string
  last_message?: string
}

// Matches ChatMessageResponse from POST /ai/chat and GET /ai/chat/history
export interface MessageDto {
  id: string
  chat_id: string
  role: "client" | "ai" | "admin"
  message: string
  created_at: string
  ticket_id?: string | null
  product?: string | null
  category?: string | null
  resolved_by_ai?: boolean
}

export interface SendMessageRequest {
  chat_id: string
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
