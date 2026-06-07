import { useQuery } from "@tanstack/react-query"
import { assistantRepository } from "data/repositories/Assistant"

export const messagesQueryKey = (sessionId: string) =>
  ["messages", sessionId] as const

export const useMessages = (sessionId: string | null) => {
  return useQuery({
    queryKey: messagesQueryKey(sessionId ?? ""),
    queryFn: () => assistantRepository.getMessages(sessionId!),
    enabled: !!sessionId,
    staleTime: 10 * 1000,
  })
}
