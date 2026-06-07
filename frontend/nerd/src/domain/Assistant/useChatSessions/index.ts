import { useQuery } from "@tanstack/react-query"
import { assistantRepository } from "data/repositories/Assistant"

export const CHAT_SESSIONS_QUERY_KEY = ["chat-sessions"] as const

export const useChatSessions = () => {
  return useQuery({
    queryKey: CHAT_SESSIONS_QUERY_KEY,
    queryFn: assistantRepository.getSessions,
    staleTime: 30 * 1000,
  })
}
