import { useQuery } from "@tanstack/react-query"
import { authRepository } from "data/repositories/Auth"

export const ME_QUERY_KEY = ["me"] as const

export const useMe = () => {
  const hasTokens = authRepository.hasTokens()
  const query = useQuery({
    queryKey: ME_QUERY_KEY,
    queryFn: authRepository.me,
    enabled: hasTokens,
    retry: false,
    staleTime: 5 * 60 * 1000,
  })

  // Без токенов не показываем закэшированного пользователя (иначе «не выходит» из аккаунта)
  return {
    ...query,
    data: hasTokens ? query.data : undefined,
    isLoading: hasTokens ? query.isLoading : false,
  }
}

export type { User } from "./types"
