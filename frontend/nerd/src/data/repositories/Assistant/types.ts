export interface ChatSession {
  id: string
  title: string
  createdAt: string
  updatedAt: string
  lastMessage?: string
  ticketId?: string | null
}

export interface Message {
  id: string
  sessionId: string
  role: "user" | "assistant"
  content: string
  createdAt: string
  ticketId?: string | null
}

export interface EscalationInfo {
  required: boolean
  suggestedProduct: string | null
  suggestedCategory: string | null
  confidence: number | null
  products: string[]
  categories: string[]
  priorities: string[]
  priorityLabels: Record<string, string>
}

export interface SendMessageResult {
  userMessage: Message
  assistantMessage: Message
  escalation: EscalationInfo | null
}

export interface CreateSessionResult {
  session: ChatSession
  messages: Message[]
  escalation: EscalationInfo | null
}

export interface EscalateChatInput {
  chatId: string
  product: string
  userPriority: string
  category?: string
  description?: string
}

export interface EscalateChatResult {
  ticketId: string
  status: string
  aiSuggestedCategory: string | null
  finalCategory: string | null
}
