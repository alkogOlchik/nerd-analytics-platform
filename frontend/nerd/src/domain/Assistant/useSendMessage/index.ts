import { useMutation, useQueryClient } from "@tanstack/react-query"
import { assistantRepository } from "data/repositories/Assistant"
import { messagesQueryKey } from "domain/Assistant/useMessages"
import { CHAT_SESSIONS_QUERY_KEY } from "domain/Assistant/useChatSessions"

export const useSendMessage = (sessionId: string | null) => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (content: string) => {
      if (!sessionId) throw new Error("No active session")
      return assistantRepository.sendMessage(sessionId, content)
    },
    onSuccess: () => {
      if (sessionId) {
        queryClient.invalidateQueries({ queryKey: messagesQueryKey(sessionId) })
      }
      queryClient.invalidateQueries({ queryKey: CHAT_SESSIONS_QUERY_KEY })
    },
  })
}
