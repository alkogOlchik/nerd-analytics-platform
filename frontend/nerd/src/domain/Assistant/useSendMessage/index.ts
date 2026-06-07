import { useMutation, useQueryClient } from "@tanstack/react-query"
import { assistantRepository } from "data/repositories/Assistant"
import type { Message } from "data/repositories/Assistant"
import { messagesQueryKey } from "domain/Assistant/useMessages"
import { CHAT_SESSIONS_QUERY_KEY } from "domain/Assistant/useChatSessions"

export const useSendMessage = (sessionId: string | null) => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ content, files }: { content: string; files?: File[] }) => {
      if (!sessionId) throw new Error("No active session")
      return assistantRepository.sendMessage(sessionId, content, files)
    },
    onMutate: async ({ content }: { content: string; files?: File[] }) => {
      if (!sessionId) return undefined
      await queryClient.cancelQueries({ queryKey: messagesQueryKey(sessionId) })
      const previousMessages = queryClient.getQueryData<Message[]>(messagesQueryKey(sessionId))
      const optimisticMessage: Message = {
        id: `opt-${Date.now()}`,
        sessionId,
        role: "user",
        content,
        createdAt: new Date().toISOString(),
      }
      queryClient.setQueryData<Message[]>(messagesQueryKey(sessionId), (old) => [
        ...(old ?? []),
        optimisticMessage,
      ])
      return { previousMessages }
    },
    onError: (_err, _content, context) => {
      if (context?.previousMessages !== undefined) {
        queryClient.setQueryData(messagesQueryKey(sessionId), context.previousMessages)
      }
    },
    onSuccess: (result) => {
      if (sessionId) {
        queryClient.setQueryData<Message[]>(messagesQueryKey(sessionId), (old) => {
          const withoutOptimistic = (old ?? []).filter((m) => !m.id.startsWith("opt-"))
          const existingIds = new Set(withoutOptimistic.map((m) => m.id))
          const toAdd = [result.userMessage, result.assistantMessage].filter(
            (m) => !existingIds.has(m.id),
          )
          return [...withoutOptimistic, ...toAdd]
        })
      }
      queryClient.invalidateQueries({ queryKey: CHAT_SESSIONS_QUERY_KEY })
    },
  })
}
