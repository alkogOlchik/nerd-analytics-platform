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
}

export interface SendMessageResult {
  userMessage: Message
  assistantMessage: Message
  escalation?: boolean
}

export interface CreateSessionResult {
  session: ChatSession
  messages: Message[]
}
