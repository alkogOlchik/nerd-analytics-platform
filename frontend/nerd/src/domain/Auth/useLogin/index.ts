import { useMutation, useQueryClient } from "@tanstack/react-query"
import { authRepository } from "data/repositories/Auth"
import { ME_QUERY_KEY } from "domain/Auth/useMe"
import type { LoginRequest } from "./types"

export const useLogin = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (req: LoginRequest) => authRepository.login(req),
    onSuccess: (user) => {
      queryClient.setQueryData(ME_QUERY_KEY, user)
    },
  })
}

export type { LoginRequest } from "./types"
