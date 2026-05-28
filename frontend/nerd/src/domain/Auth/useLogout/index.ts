import { useMutation, useQueryClient } from "@tanstack/react-query"
import { authRepository } from "data/repositories/Auth"
import { ME_QUERY_KEY } from "domain/Auth/useMe"

export const useLogout = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: authRepository.logout,
    onSuccess: () => {
      queryClient.removeQueries({ queryKey: ME_QUERY_KEY })
    },
  })
}
