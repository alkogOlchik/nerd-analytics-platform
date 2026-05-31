export interface ChatSession {
  id: string
  title: string
  createdAt: string
  updatedAt: string
  lastMessage?: string
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
}

export interface CreateSessionResult {
  session: ChatSession
  messages: Message[]
}
