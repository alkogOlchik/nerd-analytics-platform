import { useMutation, useQueryClient } from "@tanstack/react-query"
import { assistantRepository } from "data/repositories/Assistant"
import { CHAT_SESSIONS_QUERY_KEY } from "domain/Assistant/useChatSessions"

export const useEscalateToOperator = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (chatId: string) => assistantRepository.escalateToOperator(chatId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: CHAT_SESSIONS_QUERY_KEY })
    },
  })
}
