import type { QueryClient } from "@tanstack/react-query"
import { authRepository } from "data/repositories/Auth"

export const clearAuthSession = async (queryClient: QueryClient): Promise<void> => {
  await authRepository.logout()
  queryClient.clear()
}
