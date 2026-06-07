import { useMutation, useQueryClient } from "@tanstack/react-query"
import { clearAuthSession } from "domain/Auth/clearAuthSession"

export const useLogout = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: () => clearAuthSession(queryClient),
  })
}
