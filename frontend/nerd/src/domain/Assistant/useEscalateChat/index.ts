import { useMutation } from "@tanstack/react-query"
import { assistantRepository } from "data/repositories/Assistant"
import type { EscalateChatInput } from "data/repositories/Assistant"

export const useEscalateChat = () =>
  useMutation({
    mutationFn: (input: EscalateChatInput) => assistantRepository.escalateChat(input),
  })
