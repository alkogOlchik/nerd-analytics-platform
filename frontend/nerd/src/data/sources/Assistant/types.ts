export interface ChatSessionDto {
  id: string
  title: string
  ticket_id: string | null
  ticket_status: string | null
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

export interface ApiChatResponse {
  chat_id: string
  ticket_id: string | null
  ticket_status: string | null
  ticket_title: string | null
  solution_offered: boolean
  user_message: MessageDto
  assistant_message: MessageDto
  ml_response: Record<string, unknown>
  escalation: EscalationOffer | null
  video_url?: string | null
}

export interface SendMessageRequest {
  chat_id: string
  content: string
  file_ids?: string[]
}

export interface CreateSessionRequest {
  first_message: string
  file_ids?: string[]
}

export interface UploadedFileDto {
  id: string
  filename: string
  content_type: string
  size_bytes: number
  created_at: string
}

export interface EscalationOffer {
  required: boolean
  suggested_product: string | null
  suggested_category: string | null
  confidence: number | null
  products: string[]
  categories: string[]
  priorities: string[]
  priority_labels: Record<string, string>
}

export interface EscalateChatRequest {
  chat_id: string
  product: string
  user_priority: string
  category?: string
  description?: string
}

export interface EscalateChatResponse {
  ticket_id: string
  status: string
  ai_suggested_category: string | null
  final_category: string | null
}

export interface SendMessageResponse {
  user_message: MessageDto
  assistant_message: MessageDto
  ticket_id: string | null
  ticket_status: string | null
  ticket_title: string | null
  solution_offered: boolean
  escalation: EscalationOffer | null
  video_url?: string | null
}

export interface CreateSessionResponse {
  session: ChatSessionDto
  messages: MessageDto[]
  ticket_id: string | null
  ticket_status: string | null
  ticket_title: string | null
  solution_offered: boolean
  escalation: EscalationOffer | null
  video_url?: string | null
}
