import { useMutation, useQueryClient } from "@tanstack/react-query"
import { assistantRepository } from "data/repositories/Assistant"
import { CHAT_SESSIONS_QUERY_KEY } from "domain/Assistant/useChatSessions"
import { messagesQueryKey } from "domain/Assistant/useMessages"
import type { CreateSessionResult } from "data/repositories/Assistant"

export const useCreateSession = (onCreated: (result: CreateSessionResult) => void) => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (firstMessage: string) =>
      assistantRepository.createSession(firstMessage),
    onSuccess: (result) => {
      queryClient.invalidateQueries({ queryKey: CHAT_SESSIONS_QUERY_KEY })
      queryClient.setQueryData(messagesQueryKey(result.session.id), result.messages)
      onCreated(result)
    },
  })
}
