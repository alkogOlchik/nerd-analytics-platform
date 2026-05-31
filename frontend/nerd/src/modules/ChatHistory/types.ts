import type { ChatSession } from "data/repositories/Assistant"

export interface ChatHistoryProps {
  sessions: ChatSession[]
  activeSessionId: string | null
  isLoading?: boolean
  onSelect: (sessionId: string) => void
  onNewChat: () => void
}
