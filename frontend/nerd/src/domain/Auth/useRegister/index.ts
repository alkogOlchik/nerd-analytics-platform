import { useMutation, useQueryClient } from "@tanstack/react-query"
import { authRepository } from "data/repositories/Auth"
import { ME_QUERY_KEY } from "domain/Auth/useMe"
import type { RegisterRequest } from "./types"

export const useRegister = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (req: RegisterRequest) => authRepository.register(req),
    onSuccess: (user) => {
      queryClient.setQueryData(ME_QUERY_KEY, user)
    },
  })
}

export type { RegisterRequest } from "./types"
